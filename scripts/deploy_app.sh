#!/bin/bash
set -euo pipefail

# Автоматизация развёртывания приложения и сервисов в кластере после terraform apply.
# Читает параметры из infra/variables.json (создаётся terraform'ом).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VF="${ROOT_DIR}/infra/variables.json"

if [ ! -f "$VF" ]; then
    echo "Файл $VF не найден. Сначала выполните terraform apply в infra/."
    exit 1
fi

MLFLOW_TRACKING_URI="$(jq -r '.MLFLOW_TRACKING_URI' "$VF")"
S3_ACCESS_KEY="$(jq -r '.S3_ACCESS_KEY' "$VF")"
S3_SECRET_KEY="$(jq -r '.S3_SECRET_KEY' "$VF")"
S3_ENDPOINT_URL="$(jq -r '.S3_ENDPOINT_URL' "$VF")"
K8S_CLUSTER_NAME="$(jq -r '.K8S_CLUSTER_NAME' "$VF")"

echo "==> Кластер: $K8S_CLUSTER_NAME"
echo "==> MLflow: $MLFLOW_TRACKING_URI"

# 1. kubeconfig
yc managed-kubernetes cluster get-credentials "$K8S_CLUSTER_NAME" --external --force

# 2. namespace + секреты
kubectl apply -f "${ROOT_DIR}/k8s/namespace.yaml"
kubectl -n heart-api delete secret s3-creds --ignore-not-found
kubectl -n heart-api create secret generic s3-creds \
    --from-literal=AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY" \
    --from-literal=AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY"

# 3. configmap + манифесты приложения
kubectl apply -f "${ROOT_DIR}/k8s/configmap.yaml"
kubectl -n heart-api patch configmap heart-api-config --type merge \
    -p "{\"data\":{\"MLFLOW_TRACKING_URI\":\"$MLFLOW_TRACKING_URI\"}}"
kubectl apply -f "${ROOT_DIR}/k8s/deployment.yaml" \
    -f "${ROOT_DIR}/k8s/service.yaml" \
    -f "${ROOT_DIR}/k8s/hpa.yaml"

# 4. мониторинг (устанавливает CRD ServiceMonitor)
export S3_ENDPOINT_URL
export MLFLOW_TRACKING_URI
export S3_ACCESS_KEY
export S3_SECRET_KEY
bash "${ROOT_DIR}/scripts/install_monitoring.sh"
kubectl apply -f "${ROOT_DIR}/k8s/servicemonitor.yaml"

# 5. Airflow (gitSync DAGов из внешнего репозитория)
bash "${ROOT_DIR}/scripts/install_airflow.sh"

echo "==> Готово. Проверка:"
echo "    kubectl get pods -n heart-api"
echo "    kubectl get hpa -n heart-api"
