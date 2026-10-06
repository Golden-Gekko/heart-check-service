terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.119.0"
    }
  }
  required_version = ">= 1.3.0"
}

resource "yandex_iam_service_account" "k8s" {
  name      = "${var.cluster_name}-sa"
  folder_id = var.folder_id
}

resource "yandex_resourcemanager_folder_iam_member" "k8s_editor" {
  folder_id = var.folder_id
  role      = "editor"
  member    = "serviceAccount:${yandex_iam_service_account.k8s.id}"
}

resource "yandex_resourcemanager_folder_iam_member" "k8s_images_puller" {
  folder_id = var.folder_id
  role      = "container-registry.images.puller"
  member    = "serviceAccount:${yandex_iam_service_account.k8s.id}"
}

resource "yandex_kubernetes_cluster" "main" {
  name        = var.cluster_name
  description = "Kubernetes cluster for heart-api service"
  folder_id   = var.folder_id

  network_id              = var.network_id
  service_account_id      = yandex_iam_service_account.k8s.id
  node_service_account_id = yandex_iam_service_account.k8s.id

  release_channel = "REGULAR"

  master {
    version   = "1.32"
    public_ip = true

    zonal {
      zone      = var.zone
      subnet_id = var.subnet_id
    }

    security_group_ids = var.security_group_ids
  }

  depends_on = [
    yandex_resourcemanager_folder_iam_member.k8s_editor,
    yandex_resourcemanager_folder_iam_member.k8s_images_puller,
  ]
}

resource "yandex_kubernetes_node_group" "main" {
  cluster_id = yandex_kubernetes_cluster.main.id
  name       = "${var.cluster_name}-nodes"

  version = "1.32"

  instance_template {
    platform_id = "standard-v3"

    network_interface {
      nat                = true
      subnet_ids         = [var.subnet_id]
      security_group_ids = var.security_group_ids
    }

    resources {
      memory = var.node_memory
      cores  = var.node_cores
    }

    boot_disk {
      type = "network-ssd"
      size = var.node_disk_size
    }

    scheduling_policy {
      preemptible = false
    }
  }

  scale_policy {
    fixed_scale {
      size = var.node_count
    }
  }

  allocation_policy {
    location {
      zone = var.zone
    }
  }
}
