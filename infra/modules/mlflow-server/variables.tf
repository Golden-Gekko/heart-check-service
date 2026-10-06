variable "instance_user" {
  description = "Name of the user to create on the compute instance"
  type        = string
  default     = "ubuntu"
}

variable "instance_name" {
  description = "Name of the MLflow server instance"
  type        = string
}

variable "service_account_id" {
  description = "ID of the service account"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet"
  type        = string
}

variable "ubuntu_image_family" {
  description = "Ubuntu image family"
  type        = string
}

variable "public_key_path" {
  description = "Path to the public SSH key"
  type        = string
}

variable "private_key_path" {
  description = "Path to the private SSH key"
  type        = string
}

variable "s3_endpoint_url" {
  description = "S3 endpoint URL"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name for MLflow artifacts"
  type        = string
}

variable "s3_access_key" {
  description = "S3 access key"
  type        = string
}

variable "s3_secret_key" {
  description = "S3 secret key"
  type        = string
}

variable "mlflow_port" {
  description = "Port for MLflow server"
  type        = number
  default     = 5000
}
