terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.119.0"
    }
  }
  required_version = ">= 1.3.0"
}

resource "yandex_iam_service_account" "main" {
  name      = var.service_account_name
  folder_id = var.folder_id
}

resource "yandex_resourcemanager_folder_iam_member" "storage_editor" {
  folder_id = var.folder_id
  role      = "storage.editor"
  member    = "serviceAccount:${yandex_iam_service_account.main.id}"
}

resource "yandex_iam_service_account_static_access_key" "main" {
  service_account_id = yandex_iam_service_account.main.id
}

resource "yandex_kms_symmetric_key" "main" {
  name              = "${var.service_account_name}-key"
  description       = "KMS key for service account"
  default_algorithm = "AES_128"
  rotation_period   = "8760h"
}
