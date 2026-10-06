terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.119.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6.0"
    }
  }
  required_version = ">= 1.3.0"
}

resource "random_id" "bucket_id" {
  byte_length = 8
}

resource "yandex_storage_bucket" "bucket" {
  bucket        = "${var.bucket_name}-${random_id.bucket_id.hex}"
  access_key    = var.access_key
  secret_key    = var.secret_key
  force_destroy = true

  anonymous_access_flags {
    read = true
    list = true
  }
}
