terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.119.0"
    }
  }
  required_version = ">= 1.3.0"
}

resource "yandex_mdb_kafka_cluster" "kafka" {
  name               = var.cluster_name
  environment        = "PRODUCTION"
  network_id         = var.network_id
  subnet_ids         = var.subnet_ids
  security_group_ids = var.security_group_ids

  config {
    version          = var.kafka_version
    brokers_count    = 1
    zones            = [var.zone]
    assign_public_ip = var.assign_public_ip
    schema_registry  = false

    kafka {
      resources {
        resource_preset_id = var.resource_preset_id
        disk_type_id       = "network-ssd"
        disk_size          = var.disk_size
      }
      kafka_config {
        sasl_enabled_mechanisms = ["SASL_MECHANISM_SCRAM_SHA_512"]
      }
    }
  }
}

resource "yandex_mdb_kafka_topic" "inputs" {
  cluster_id         = yandex_mdb_kafka_cluster.kafka.id
  name               = var.input_topic
  partitions         = 3
  replication_factor = 1
}

resource "yandex_mdb_kafka_topic" "predictions" {
  cluster_id         = yandex_mdb_kafka_cluster.kafka.id
  name               = var.output_topic
  partitions         = 3
  replication_factor = 1
}

resource "yandex_mdb_kafka_user" "producer" {
  cluster_id = yandex_mdb_kafka_cluster.kafka.id
  name       = var.producer_user
  password   = var.producer_password

  permission {
    topic_name = yandex_mdb_kafka_topic.inputs.name
    role       = "ACCESS_ROLE_PRODUCER"
  }
}

resource "yandex_mdb_kafka_user" "consumer" {
  cluster_id = yandex_mdb_kafka_cluster.kafka.id
  name       = var.consumer_user
  password   = var.consumer_password

  permission {
    topic_name = yandex_mdb_kafka_topic.inputs.name
    role       = "ACCESS_ROLE_CONSUMER"
  }

  permission {
    topic_name = yandex_mdb_kafka_topic.predictions.name
    role       = "ACCESS_ROLE_PRODUCER"
  }

  permission {
    topic_name = yandex_mdb_kafka_topic.predictions.name
    role       = "ACCESS_ROLE_CONSUMER"
  }
}
