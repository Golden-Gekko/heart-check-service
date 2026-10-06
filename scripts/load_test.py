import argparse
import json
import logging
import os
import random
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Any

import requests
from kafka import KafkaConsumer, KafkaProducer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('load_test')

CA_CERT_URL = 'https://storage.yandexcloud.net/cloud-certs/CA.pem'


def download_ca_cert(path: str) -> str:
    if os.path.exists(path):
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    response = requests.get(CA_CERT_URL, timeout=30)
    response.raise_for_status()
    with open(path, 'wb') as f:
        f.write(response.content)
    return path


def build_kafka_config(
    args: argparse.Namespace, username: str, password: str
) -> dict[str, Any]:
    config = {
        'bootstrap_servers': args.bootstrap_servers.split(','),
        'security_protocol': args.security_protocol,
        'sasl_mechanism': args.sasl_mechanism,
        'sasl_plain_username': username,
        'sasl_plain_password': password,
    }
    if args.security_protocol.endswith('SSL'):
        ca_path = download_ca_cert(args.ssl_ca_path)
        config['ssl_cafile'] = ca_path
    return config


def generate_patient(patient_id: int) -> dict[str, Any]:
    rng = random.Random(patient_id)
    return {
        'diabetes': rng.random() < 0.5,
        'family_history': rng.random() < 0.5,
        'obesity': rng.random() < 0.5,
        'alcohol_consumption': rng.random() < 0.5,
        'previous_heart_problems': rng.random() < 0.5,
        'medication_use': rng.random() < 0.5,
        'diet': rng.randrange(0, 3),
        'stress_level': rng.randrange(1, 11),
        'physical_activity_days_per_week': rng.randrange(0, 8),
        'age': round(rng.random(), 4),
        'cholesterol': round(rng.random(), 4),
        'heart_rate': round(rng.random(), 4),
        'exercise_hours_per_week': round(rng.random(), 4),
        'sedentary_hours_per_day': round(rng.random(), 4),
        'bmi': round(rng.random(), 4),
        'triglycerides': round(rng.random(), 4),
        'blood_sugar': round(rng.random(), 4),
        'ck_mb': round(rng.random(), 4),
        'troponin': round(rng.random(), 4),
        'systolic_blood_pressure': round(rng.random(), 4),
        'diastolic_blood_pressure': round(rng.random(), 4),
        'sleep_hours_per_day': round(rng.random(), 4),
    }


class ProducerThread(threading.Thread):
    def __init__(self, args: argparse.Namespace, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.args = args
        self.stop_event = stop_event
        self.sent = 0
        self.producer: KafkaProducer | None = None

    def run(self) -> None:
        config = build_kafka_config(self.args, self.args.kafka_user, self.args.kafka_password)
        self.producer = KafkaProducer(
            **config,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v: str(v).encode('utf-8'),
        )
        rate = self.args.start_rate
        tx_id = 1
        logger.info(
            'Producer стартовал: start_rate=%s msg/s, ramp_step=%s, ramp_interval=%ss',
            self.args.start_rate,
            self.args.ramp_step,
            self.args.ramp_interval,
        )
        while not self.stop_event.is_set():
            start = time.time()
            for _ in range(rate):
                if self.stop_event.is_set():
                    break
                transaction = generate_patient(tx_id)
                self.producer.send(
                    self.args.topic,
                    key=tx_id,
                    value=transaction,
                )
                tx_id += 1
                self.sent += 1
            self.producer.flush()
            elapsed = time.time() - start
            sleep_time = max(0.0, 1.0 - elapsed)
            self.stop_event.wait(sleep_time)

            if tx_id % self.args.ramp_interval == 0:
                rate = min(rate + self.args.ramp_step, self.args.max_rate)
                logger.info('RAMP: текущая скорость %s msg/s', rate)


class ConsumerThread(threading.Thread):
    def __init__(self, args: argparse.Namespace, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.args = args
        self.stop_event = stop_event
        self.processed = 0
        self.errors = 0
        self.latencies: list[float] = []
        self.workers = args.workers

    def _call_api(self, value: dict[str, Any]) -> tuple[bool, float]:
        start = time.time()
        try:
            response = requests.post(
                self.args.api_url,
                json={'patients': [value]},
                timeout=30,
            )
            response.raise_for_status()
            return True, time.time() - start
        except Exception as exc:
            logger.warning('Ошибка вызова API: %s', exc)
            return False, time.time() - start

    def _record(self, futures: set) -> None:
        for future in futures:
            try:
                ok, latency = future.result()
            except Exception:
                ok, latency = False, 0.0
            if ok:
                self.processed += 1
            else:
                self.errors += 1
            self.latencies.append(latency)

    def run(self) -> None:
        config = build_kafka_config(
            self.args, self.args.kafka_consumer_user, self.args.kafka_consumer_password
        )
        config['group_id'] = self.args.consumer_group
        config['auto_offset_reset'] = 'latest'
        config['value_deserializer'] = lambda v: json.loads(v.decode('utf-8'))
        consumer = KafkaConsumer(self.args.topic, **config)
        logger.info(
            'Consumer стартовал, API URL: %s, workers: %s',
            self.args.api_url,
            self.workers,
        )
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            pending: set = set()
            max_pending = self.workers * 8
            for message in consumer:
                if self.stop_event.is_set():
                    break
                pending.add(executor.submit(self._call_api, message.value))
                if len(pending) >= max_pending:
                    done, pending = wait(pending, return_when=FIRST_COMPLETED)
                    self._record(done)
            self._record(pending)
        consumer.close()


def stats_loop(
    producer: ProducerThread,
    consumer: ConsumerThread,
    stop_event: threading.Event,
    interval: int,
) -> None:
    while not stop_event.is_set():
        stop_event.wait(interval)
        latencies = consumer.latencies[-1000:]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        logger.info(
            'Sent=%s Processed=%s Errors=%s AvgLatency=%.3fs',
            producer.sent,
            consumer.processed,
            consumer.errors,
            avg_latency,
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Нагрузочный тест через Kafka и REST API'
    )
    parser.add_argument(
        '--bootstrap-servers',
        default=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9091'),
    )
    parser.add_argument(
        '--topic',
        default=os.getenv('KAFKA_INPUT_TOPIC', 'inputs'),
    )
    parser.add_argument(
        '--kafka-user',
        default=os.getenv('KAFKA_PRODUCER_USER', 'producer'),
    )
    parser.add_argument(
        '--kafka-password',
        default=os.getenv('KAFKA_PRODUCER_PASSWORD', 'ProducerPass123!'),
    )
    parser.add_argument(
        '--kafka-consumer-user',
        default=os.getenv('KAFKA_CONSUMER_USER', 'consumer'),
    )
    parser.add_argument(
        '--kafka-consumer-password',
        default=os.getenv('KAFKA_CONSUMER_PASSWORD', 'ConsumerPass123!'),
    )
    parser.add_argument(
        '--security-protocol',
        default=os.getenv('KAFKA_SECURITY_PROTOCOL', 'SASL_SSL'),
    )
    parser.add_argument(
        '--sasl-mechanism',
        default=os.getenv('KAFKA_SASL_MECHANISM', 'SCRAM-SHA-512'),
    )
    parser.add_argument(
        '--ssl-ca-path',
        default=os.getenv('KAFKA_SSL_CA_PATH', './YandexInternalRootCA.crt'),
    )
    parser.add_argument(
        '--api-url',
        default=os.getenv('API_URL', 'http://localhost:30080/predict'),
    )
    parser.add_argument('--consumer-group', default='load-test-consumer')
    parser.add_argument(
        '--workers',
        type=int,
        default=16,
        help='Количество потоков для вызова API (конкурентность)',
    )
    parser.add_argument(
        '--start-rate', type=int, default=10, help='Начальная скорость msg/s'
    )
    parser.add_argument(
        '--max-rate', type=int, default=1000, help='Максимальная скорость msg/s'
    )
    parser.add_argument(
        '--ramp-step', type=int, default=10, help='Шаг наращивания скорости'
    )
    parser.add_argument(
        '--ramp-interval',
        type=int,
        default=100,
        help='Количество сообщений между ramp',
    )
    parser.add_argument(
        '--duration', type=int, default=600, help='Длительность теста в секундах'
    )
    parser.add_argument(
        '--stats-interval',
        type=int,
        default=30,
        help='Интервал статистики в секундах',
    )
    args = parser.parse_args()

    stop_event = threading.Event()
    producer = ProducerThread(args, stop_event)
    consumer = ConsumerThread(args, stop_event)

    producer.start()
    consumer.start()

    stats_thread = threading.Thread(
        target=stats_loop,
        args=(producer, consumer, stop_event, args.stats_interval),
        daemon=True,
    )
    stats_thread.start()

    logger.info(
        'Тест запущен на %s секунд. Нажмите Ctrl+C для остановки.', args.duration
    )
    try:
        stop_event.wait(args.duration)
    except KeyboardInterrupt:
        logger.info('Получен сигнал остановки')
    finally:
        stop_event.set()
        producer.join(timeout=5)
        consumer.join(timeout=5)
        logger.info(
            'Финальная статистика: Sent=%s Processed=%s Errors=%s',
            producer.sent,
            consumer.processed,
            consumer.errors,
        )


if __name__ == '__main__':
    main()
