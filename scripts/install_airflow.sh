#!/bin/bash
set -e

# Установка Apache Airflow в кластер Yandex Managed Kubernetes.
# Запускать после получения credentials и настройки kubectl.
# Инжектирует MLFLOW_TRACKING_URI и S3-креды из infra/variables.json (или из env).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAMESPACE="${NAMESPACE:-airflow}"
VALUES_FILE="${1:-${ROOT_DIR}/k8s/airflow/values.yaml}"
CHART_VERSION="${CHART_VERSION:-1.16.0}"

if ! command -v helm &> /dev/null; then
    echo "Helm не найден. Установите helm: https://helm.sh/docs/intro/install/"
    exit 1
fi

VF="${ROOT_DIR}/infra/variables.json"
if [ -f "$VF" ]; then
    MLFLOW_TRACKING_URI="$(jq -r '.MLFLOW_TRACKING_URI' "$VF")"
    AWS_ACCESS_KEY_ID="$(jq -r '.S3_ACCESS_KEY' "$VF")"
    AWS_SECRET_ACCESS_KEY="$(jq -r '.S3_SECRET_KEY' "$VF")"
    MLFLOW_S3_ENDPOINT_URL="$(jq -r '.S3_ENDPOINT_URL' "$VF")"
    S3_BUCKET="$(jq -r '.S3_BUCKET_NAME' "$VF")"
else
    MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-http://heart-api-mlflow:5000}"
    AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
    AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"
    MLFLOW_S3_ENDPOINT_URL="${MLFLOW_S3_ENDPOINT_URL:-https://storage.yandexcloud.net}"
    S3_BUCKET="${S3_BUCKET:-}"
fi

AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-ru-central1}"
S3_KEY="${S3_KEY:-datasets/heart_train.csv}"

helm repo add apache-airflow https://airflow.apache.org || true
helm repo update

ENV_VALUES="$(mktemp)"
trap 'rm -f "$ENV_VALUES"' EXIT

cat > "$ENV_VALUES" <<EOF
env:
  - name: MLFLOW_TRACKING_URI
    value: "${MLFLOW_TRACKING_URI}"
  - name: AWS_ACCESS_KEY_ID
    value: "${AWS_ACCESS_KEY_ID}"
  - name: AWS_SECRET_ACCESS_KEY
    value: "${AWS_SECRET_ACCESS_KEY}"
  - name: MLFLOW_S3_ENDPOINT_URL
    value: "${MLFLOW_S3_ENDPOINT_URL}"
  - name: AWS_DEFAULT_REGION
    value: "${AWS_DEFAULT_REGION}"
  - name: S3_BUCKET
    value: "${S3_BUCKET}"
  - name: S3_KEY
    value: "${S3_KEY}"
EOF

helm upgrade --install airflow apache-airflow/airflow \
    --version "$CHART_VERSION" \
    -n "$NAMESPACE" \
    --create-namespace \
    -f "$VALUES_FILE" \
    -f "$ENV_VALUES"

echo "Airflow установлен в namespace $NAMESPACE"
echo "Airflow UI: http://<NODE_IP>:30081 (admin / admin)"
