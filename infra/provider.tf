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
    local = {
      source  = "hashicorp/local"
      version = ">= 2.5.0"
    }
  }
  required_version = ">= 1.3.0"
}

provider "yandex" {
  token     = var.yc_config.token
  cloud_id  = var.yc_config.cloud_id
  folder_id = var.yc_config.folder_id
  zone      = var.yc_config.zone
}
