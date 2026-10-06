import argparse
import logging
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('upload_data')

DEFAULT_FILE = Path(__file__).resolve().parent.parent / 'data' / 'heart_train.csv'


def parse_args() -> argparse.Namespace:
    parser = ArgumentParser(description='Загрузка датасета heart в S3-бакет')
    parser.add_argument('--file', default=str(DEFAULT_FILE))
    parser.add_argument('--bucket', default=os.getenv('S3_BUCKET'))
    parser.add_argument('--key', default='datasets/heart_train.csv')
    parser.add_argument(
        '--endpoint-url',
        default=os.getenv('MLFLOW_S3_ENDPOINT_URL')
        or os.getenv('AWS_ENDPOINT_URL'),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.bucket:
        raise SystemExit('Не задан бакет: укажите --bucket или переменную S3_BUCKET')

    local_path = Path(args.file)
    if not local_path.is_file():
        raise SystemExit(f'Файл не найден: {local_path}')

    client = boto3.client(
        's3',
        endpoint_url=args.endpoint_url,
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    )

    logger.info('Загрузка %s -> s3://%s/%s', local_path, args.bucket, args.key)
    try:
        client.upload_file(str(local_path), args.bucket, args.key)
    except (BotoCoreError, ClientError) as exc:
        raise SystemExit(f'Ошибка загрузки в S3: {exc}') from exc

    logger.info('Готово')


if __name__ == '__main__':
    main()
