variable "yc_config" {
  description = "Yandex Cloud configuration"
  type = object({
    token     = string
    cloud_id  = string
    folder_id = string
    zone      = string
  })
  sensitive = true
}

variable "cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
  default     = "heart-api-k8s"
}

variable "node_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 3
}

variable "node_cores" {
  description = "vCPU per worker node"
  type        = number
  default     = 4
}

variable "node_memory" {
  description = "Memory per worker node in GB"
  type        = number
  default     = 16
}

variable "node_disk_size" {
  description = "Disk size for worker nodes in GB"
  type        = number
  default     = 50
}

variable "network_cidr" {
  description = "CIDR for the Kubernetes cluster network"
  type        = string
  default     = "10.200.0.0/16"
}

variable "yc_service_account_name" {
  description = "Name of the Yandex Cloud service account"
  type        = string
  default     = "heart-api-sa"
}

variable "yc_bucket_name" {
  description = "Prefix for the S3 bucket name"
  type        = string
  default     = "heart-api-bucket"
}

variable "yc_storage_endpoint_url" {
  description = "Yandex Object Storage endpoint"
  type        = string
  default     = "https://storage.yandexcloud.net"
}

variable "yc_mlflow_instance_name" {
  description = "Name of the MLflow server instance"
  type        = string
  default     = "heart-api-mlflow"
}

variable "yc_kafka_cluster_name" {
  description = "Name of the Managed Kafka cluster"
  type        = string
  default     = "heart-api-kafka"
}

variable "kafka_producer_password" {
  description = "Password for Kafka producer user"
  type        = string
  sensitive   = true
}

variable "kafka_consumer_password" {
  description = "Password for Kafka consumer user"
  type        = string
  sensitive   = true
}

variable "ubuntu_image_family" {
  description = "Ubuntu image family for MLflow server"
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "public_key_path" {
  description = "Path to the public SSH key"
  type        = string
}

variable "private_key_path" {
  description = "Path to the private SSH key"
  type        = string
}
