# Helm values for kube-prometheus-stack
# Variables: admin_email, smtp_smarthost, smtp_from, smtp_auth_username,
#            smtp_auth_password, grafana_admin_password

prometheus:
  prometheusSpec:
    retention: 7d
    enableAdminAPI: false
    serviceMonitorSelectorNilUsesHelmValues: false
    podMonitorSelectorNilUsesHelmValues: false
    resources:
      requests:
        cpu: 250m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 2Gi
    storageSpec:
      emptyDir:
        medium: ""

alertmanager:
  config:
    global:
      smtp_smarthost: "${smtp_smarthost}"
      smtp_from: "${smtp_from}"
      smtp_auth_username: "${smtp_auth_username}"
      smtp_auth_password: "${smtp_auth_password}"
      smtp_require_tls: true
    route:
      receiver: "email-admin"
      group_by: ["alertname", "namespace", "pod"]
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 12h
    receivers:
      - name: "email-admin"
        email_configs:
          - to: "${admin_email}"
            send_resolved: true
            headers:
              Subject: "[MLOps Alert] {{ .GroupLabels.alertname }}"
  alertmanagerSpec:
    resources:
      requests:
        cpu: 50m
        memory: 128Mi
      limits:
        cpu: 200m
        memory: 512Mi

defaultRules:
  create: true

additionalPrometheusRulesMap:
  heart-api-rules:
    groups:
      - name: heart-api
        rules:
          - alert: HeartAPIHighLoad
            expr: |
              (
                kube_deployment_status_replicas{deployment="heart-api"} == 6
              )
              and on()
              (
                max(
                  rate(container_cpu_usage_seconds_total{pod=~"heart-api-.*"}[2m])
                )
                /
                max(
                  kube_pod_container_resource_limits{resource="cpu", container="heart-api"}
                )
                > 0.8
              )
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "Heart API pod CPU above 80% for 5 minutes with 6 replicas"
              description: |
                Deployment heart-api развернут в 6 реплик и CPU хотя бы одного пода
                превышает 80% в течение 5 минут. Возможна DDoS-атака или пиковая нагрузка.

grafana:
  enabled: true
  adminPassword: "${grafana_admin_password}"
  service:
    type: NodePort
    nodePort: 30300
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi

kubeStateMetrics:
  enabled: true

nodeExporter:
  enabled: true

prometheusOperator:
  resources:
    requests:
      cpu: 50m
      memory: 128Mi
    limits:
      cpu: 200m
      memory: 512Mi
