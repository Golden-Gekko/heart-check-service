variable "folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud zone"
  type        = string
}

variable "cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
}

variable "node_count" {
  description = "Number of worker nodes"
  type        = number
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
}

variable "subnet_id" {
  description = "Subnet ID for the cluster"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs"
  type        = list(string)
}

variable "network_id" {
  description = "VPC network ID"
  type        = string
}
