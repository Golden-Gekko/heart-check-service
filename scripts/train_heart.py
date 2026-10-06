import argparse
import logging
import os
import sys
import tempfile
from argparse import ArgumentParser
from pathlib import Path
from urllib.parse import urlparse

import mlflow
from mlflow.tracking import MlflowClient
from pyspark.ml import Pipeline
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.feature import StandardScaler, VectorAssembler
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.features import (  # noqa: E402
    MODEL_FEATURE_COLS,
    normalize_columns,
    prepare_features,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('train_heart')

DEFAULT_CSV = Path(__file__).resolve().parent.parent / 'data' / 'heart_train.csv'
RAW_TARGET_COL = 'heart_attack_risk_binary'
TARGET_COL = 'target'


def build_pipeline(seed: int) -> Pipeline:
    stages = [
        VectorAssembler(
            inputCols=MODEL_FEATURE_COLS,
            outputCol='features_raw',
            handleInvalid='skip',
        ),
        StandardScaler(
            inputCol='features_raw',
            outputCol='features',
            withStd=True,
            withMean=True,
        ),
        RandomForestClassifier(
            labelCol=TARGET_COL,
            featuresCol='features',
            numTrees=20,
            maxDepth=5,
            seed=seed,
        ),
    ]
    return Pipeline(stages=stages)


def resolve_tracking_uri(uri: str) -> str:
    if uri.startswith('file:'):
        path = Path(uri[len('file:'):])
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.resolve().as_uri()
    return uri


def download_from_s3(uri: str) -> Path:
    import boto3

    parsed = urlparse(uri)
    bucket = parsed.netloc
    key = parsed.path.lstrip('/')
    endpoint = os.getenv('MLFLOW_S3_ENDPOINT_URL') or os.getenv('AWS_ENDPOINT_URL')
    target = Path(tempfile.gettempdir()) / Path(key).name
    logger.info('Скачивание %s -> %s', uri, target)
    client = boto3.client('s3', endpoint_url=endpoint)
    client.download_file(bucket, key, str(target))
    return target


def load_dataframe(spark: SparkSession, args: argparse.Namespace) -> DataFrame:
    if args.s3_uri:
        csv_path = download_from_s3(args.s3_uri)
    else:
        csv_path = Path(args.local_csv)

    logger.info('Чтение данных: %s', csv_path)
    raw = spark.read.csv(str(csv_path), header=True, inferSchema=True)
    df = normalize_columns(raw)
    df = prepare_features(df)
    return df.withColumn(TARGET_COL, col(RAW_TARGET_COL).cast('int')).select(
        *MODEL_FEATURE_COLS, TARGET_COL
    )


def register_model(model_name: str, alias: str) -> str:
    client = MlflowClient()
    versions = client.search_model_versions(f"name='{model_name}'")
    latest = max(versions, key=lambda v: int(v.version))
    client.set_registered_model_alias(model_name, alias, latest.version)
    return latest.version


def parse_args() -> argparse.Namespace:
    parser = ArgumentParser(description='Обучение heart-модели (PySpark + MLflow)')
    parser.add_argument('--local-csv', default=str(DEFAULT_CSV))
    parser.add_argument('--s3-uri', default=None)
    parser.add_argument('--tracking-uri', default=settings.mlflow_tracking_uri)
    parser.add_argument('--experiment', default='heart_attack')
    parser.add_argument('--output', default='models/heart')
    parser.add_argument('--model-name', default=settings.mlflow_model_name)
    parser.add_argument('--alias', default=settings.mlflow_model_alias)
    parser.add_argument('--seed', type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    spark = (
        SparkSession.builder.appName('train-heart')
        .master('local[*]')
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel('WARN')

    try:
        df = load_dataframe(spark, args)
        train_df, test_df = df.randomSplit([0.8, 0.2], seed=args.seed)

        model = build_pipeline(args.seed).fit(train_df)

        predictions = model.transform(test_df)
        auc = BinaryClassificationEvaluator(
            labelCol=TARGET_COL,
            rawPredictionCol='rawPrediction',
            metricName='areaUnderROC',
        ).evaluate(predictions)
        logger.info('Test AUC: %.4f', auc)

        tracking_uri = resolve_tracking_uri(args.tracking_uri)
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(args.experiment)
        with mlflow.start_run(run_name='heart_random_forest'):
            mlflow.log_param('rows', df.count())
            mlflow.log_param('seed', args.seed)
            mlflow.log_param('model_name', args.model_name)
            mlflow.log_metric('test_auc', auc)
            mlflow.spark.log_model(
                model,
                artifact_path='model',
                registered_model_name=args.model_name,
            )

        version = register_model(args.model_name, args.alias)
        logger.info('Alias @%s -> версия %s', args.alias, version)

        model.write().overwrite().save(args.output)
        logger.info('Модель сохранена: %s', args.output)
        logger.info(
            'Готово: models:/%s@%s (tracking: %s)',
            args.model_name,
            args.alias,
            tracking_uri,
        )
    finally:
        spark.stop()


if __name__ == '__main__':
    main()
