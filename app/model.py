import logging
import tempfile
from pathlib import Path
from typing import Any

import mlflow
from pyspark.ml import PipelineModel
from pyspark.ml.functions import vector_to_array
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, monotonically_increasing_id

from app.config import settings
from app.features import (
    INPUT_SCHEMA,
    normalize_columns,
    prepare_features,
)
from app.lag import cpu_lag

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self) -> None:
        self._spark: SparkSession | None = None
        self._model: PipelineModel | None = None
        self._ready: bool = False

    def _create_spark_session(self) -> SparkSession:
        logger.info('Создание SparkSession в local mode')
        return (
            SparkSession.builder.appName('heart-api')
            .master('local[*]')
            .config('spark.sql.adaptive.enabled', 'false')
            .config('spark.hadoop.fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem')
            .getOrCreate()
        )

    def _resolve_tracking_uri(self) -> str:
        uri = settings.mlflow_tracking_uri
        if uri.startswith('file:'):
            path = Path(uri[len('file:'):])
            if not path.is_absolute():
                path = Path.cwd() / path
            return path.resolve().as_uri()
        return uri

    def _resolve_model_uri(self) -> str:
        return f'models:/{settings.mlflow_model_name}@{settings.mlflow_model_alias}'

    def load_model(self) -> None:
        if self._ready:
            return

        tracking_uri = self._resolve_tracking_uri()
        mlflow.set_tracking_uri(tracking_uri)

        model_uri = self._resolve_model_uri()
        logger.info('Загрузка модели из MLflow (%s): %s', tracking_uri, model_uri)

        local_dir = mlflow.artifacts.download_artifacts(artifact_uri=model_uri)
        logger.info('Артефакт модели скачан: %s', local_dir)

        self._spark = self._create_spark_session()
        self._model = mlflow.spark.load_model(local_dir)
        self._ready = True
        logger.info('Модель успешно загружена')

    @property
    def ready(self) -> bool:
        return self._ready

    def _extract_probabilities(self, df: DataFrame) -> list[float]:
        preds = self._model.transform(df)
        rows = (
            preds.withColumn('probability_arr', vector_to_array(col('probability')))
            .select(col('probability_arr')[1].alias('probability'))
            .collect()
        )
        return [float(row.probability) for row in rows]

    def predict_patients(self, patients: list[dict]) -> list[float]:
        """Возвращает вероятность высокого риска для каждого пациента."""
        if not self._ready:
            self.load_model()

        df = self._spark.createDataFrame(patients, schema=INPUT_SCHEMA)
        probabilities = self._extract_probabilities(prepare_features(df))

        # Искусственная задержка для имитации тяжёлой модели.
        cpu_lag(settings.cpu_lag_ticks)

        return probabilities

    def predict_csv(self, content: bytes) -> list[dict[str, Any]]:
        """Предсказания для CSV-файла в формате workshop (id + 22 признака)."""
        if not self._ready:
            self.load_model()

        with tempfile.NamedTemporaryFile('wb', suffix='.csv', delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            raw = self._spark.read.csv(tmp_path.as_uri(), header=True, inferSchema=True)
            df = normalize_columns(raw)
            if 'id' in df.columns:
                df = df.withColumn('_row_id', col('id'))
            else:
                df = df.withColumn('_row_id', monotonically_increasing_id())

            preds = self._model.transform(prepare_features(df))
            rows = (
                preds.withColumn('probability_arr', vector_to_array(col('probability')))
                .select(
                    col('_row_id').alias('id'),
                    col('probability_arr')[1].alias('probability'),
                )
                .collect()
            )
        finally:
            tmp_path.unlink(missing_ok=True)

        cpu_lag(settings.cpu_lag_ticks)

        return [
            {'id': row.id, 'predict': round(float(row.probability) * 100, 2)}
            for row in rows
        ]

    def health(self) -> dict[str, Any]:
        return {
            'status': 'healthy',
            'model_loaded': self._ready,
            'model_name': settings.mlflow_model_name,
            'model_alias': settings.mlflow_model_alias,
        }
