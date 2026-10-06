output "k8s_cluster_id" {
  value = module.k8s.cluster_id
}

output "k8s_cluster_name" {
  value = module.k8s.cluster_name
}

output "mlflow_tracking_uri" {
  value = module.mlflow-server.mlflow_tracking_uri
}

output "mlflow_external_ip" {
  value = module.mlflow-server.external_ip_address
}

output "kafka_bootstrap_servers" {
  value = module.kafka-cluster.bootstrap_servers
}

output "kafka_input_topic" {
  value = module.kafka-cluster.input_topic
}

output "s3_bucket_name" {
  value = module.storage.bucket
}
