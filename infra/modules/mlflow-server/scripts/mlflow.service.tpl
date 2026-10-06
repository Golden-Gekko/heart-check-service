[Unit]
Description=MLflow Tracking Server
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu
EnvironmentFile=/home/ubuntu/.mlflow.conf
ExecStart=/home/ubuntu/venv/bin/mlflow server --host 0.0.0.0 --port ${mlflow_port} --backend-store-uri sqlite:////home/ubuntu/mlflow.db --default-artifact-root s3://${s3_bucket_name}/mlflow/artifacts
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
