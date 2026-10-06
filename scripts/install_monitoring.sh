#!/bin/bash
set -e

# Установка kube-prometheus-stack в кластер Yandex Managed Kubernetes.
# Запускать после получения credentials и настройки kubectl.

NAMESPACE="${NAMESPACE:-monitoring}"
CHART_VERSION="${CHART_VERSION:-58.0.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VALUES_FILE="${1:-${ROOT_DIR}/k8s/monitoring/values.yaml.tpl}"

if ! command -v helm &> /dev/null; then
    echo "Helm не найден. Установите helm: https://helm.sh/docs/intro/install/"
    exit 1
fi

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
helm repo update

# Генерируем values из шаблона через envsubst.
export ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
export SMTP_SMARTHOST="${SMTP_SMARTHOST:-smtp.yandex.ru:465}"
export SMTP_FROM="${SMTP_FROM:-alerts@example.com}"
export SMTP_AUTH_USERNAME="${SMTP_AUTH_USERNAME:-alerts@example.com}"
export SMTP_AUTH_PASSWORD="${SMTP_AUTH_PASSWORD:-password}"
export GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin}"

VALUES_RENDERED="$(mktemp)"
envsubst < "$VALUES_FILE" > "$VALUES_RENDERED"

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
    --version "$CHART_VERSION" \
    -n "$NAMESPACE" \
    --create-namespace \
    -f "$VALUES_RENDERED"

rm -f "$VALUES_RENDERED"

echo "Monitoring stack установлен в namespace $NAMESPACE"
echo "Grafana: http://<NODE_IP>:30300 (admin / $GRAFANA_ADMIN_PASSWORD)"
echo "Prometheus: kubectl port-forward svc/kube-prometheus-stack-prometheus -n $NAMESPACE 9090"
echo "Alertmanager: kubectl port-forward svc/kube-prometheus-stack-alertmanager -n $NAMESPACE 9093"
