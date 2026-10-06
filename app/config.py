import os


class Settings:
    def __init__(self):
        self.app_name: str = os.getenv('APP_NAME', 'heart-api')
        self.app_host: str = os.getenv('APP_HOST', '0.0.0.0')
        self.app_port: int = int(os.getenv('APP_PORT', '8000'))
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')

        self.mlflow_tracking_uri: str = os.getenv(
            'MLFLOW_TRACKING_URI', 'file:./mlruns'
        )
        self.mlflow_model_name: str = os.getenv(
            'MLFLOW_MODEL_NAME', 'heart_attack_rf'
        )
        self.mlflow_model_alias: str = os.getenv(
            'MLFLOW_MODEL_ALIAS', 'champion'
        )

        # Искусственная нагрузка на CPU внутри /predict.
        # Количество "тиков" busy-loop на одного пациента.
        self.cpu_lag_ticks: int = int(os.getenv('CPU_LAG_TICKS', '150000'))


settings = Settings()
