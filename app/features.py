import re

from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    StructField,
    StructType,
)

BINARY_COLS = [
    'diabetes',
    'family_history',
    'obesity',
    'alcohol_consumption',
    'previous_heart_problems',
    'medication_use',
]

CATEGORY_COLS = [
    'diet',
    'stress_level',
    'physical_activity_days_per_week',
]

NUMERIC_COLS = [
    'age',
    'cholesterol',
    'heart_rate',
    'exercise_hours_per_week',
    'sedentary_hours_per_day',
    'bmi',
    'triglycerides',
    'blood_sugar',
    'ck_mb',
    'troponin',
    'systolic_blood_pressure',
    'diastolic_blood_pressure',
    'sleep_hours_per_day',
]

MODEL_FEATURE_COLS = BINARY_COLS + CATEGORY_COLS + NUMERIC_COLS

INPUT_SCHEMA = StructType(
    [StructField(name, BooleanType(), True) for name in BINARY_COLS]
    + [StructField(name, IntegerType(), True) for name in CATEGORY_COLS]
    + [StructField(name, DoubleType(), True) for name in NUMERIC_COLS]
)


def normalize_columns(df: DataFrame) -> DataFrame:
    """Приводит имена колонок DataFrame к snake_case."""
    for name in df.columns:
        new_name = (
            re.sub(r'[()]', '', name).lower().replace(' ', '_').replace('-', '_')
        )
        if new_name != name:
            df = df.withColumnRenamed(name, new_name)
    return df


def prepare_features(df: DataFrame) -> DataFrame:
    """Приводит признаки модели к DoubleType, сохраняя остальные колонки."""
    for name in MODEL_FEATURE_COLS:
        df = df.withColumn(name, col(name).cast(DoubleType()))
    return df
