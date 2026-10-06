variable "cluster_name" {
  type        = string
  description = "Name of the Managed Kafka cluster"
}

variable "network_id" {
  type        = string
  description = "VPC network ID"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for Kafka brokers"
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security group IDs"
}

variable "zone" {
  type        = string
  description = "Availability zone"
}

variable "kafka_version" {
  type        = string
  description = "Apache Kafka version"
  default     = "3.9"
}

variable "resource_preset_id" {
  type        = string
  description = "Broker resource preset"
  default     = "s2.micro"
}

variable "disk_size" {
  type        = number
  description = "Broker disk size in GB"
  default     = 32
}

variable "assign_public_ip" {
  type        = bool
  description = "Assign public IP to brokers (needed for external producers)"
  default     = true
}

variable "input_topic" {
  type        = string
  default     = "inputs"
}

variable "output_topic" {
  type        = string
  default     = "predictions"
}

variable "producer_user" {
  type        = string
  default     = "producer"
}

variable "consumer_user" {
  type        = string
  default     = "consumer"
}

variable "producer_password" {
  type        = string
  sensitive   = true
}

variable "consumer_password" {
  type        = string
  sensitive   = true
}
