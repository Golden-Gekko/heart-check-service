output "cluster_id" {
  value = yandex_mdb_kafka_cluster.kafka.id
}

output "hosts" {
  value = [
    for h in yandex_mdb_kafka_cluster.kafka.host : "${h.name}:9091"
  ]
}

output "bootstrap_servers" {
  value = join(",", [
    for h in yandex_mdb_kafka_cluster.kafka.host : "${h.name}:9091"
  ])
}

output "input_topic" {
  value = yandex_mdb_kafka_topic.inputs.name
}

output "output_topic" {
  value = yandex_mdb_kafka_topic.predictions.name
}

output "producer_user" {
  value = yandex_mdb_kafka_user.producer.name
}

output "consumer_user" {
  value = yandex_mdb_kafka_user.consumer.name
}

output "producer_password" {
  value     = var.producer_password
  sensitive = true
}

output "consumer_password" {
  value     = var.consumer_password
  sensitive = true
}
