terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.119.0"
    }
  }
  required_version = ">= 1.3.0"
}

data "yandex_compute_image" "ubuntu_image" {
  family = var.ubuntu_image_family
}

resource "yandex_compute_instance" "mlflow_server" {
  name               = var.instance_name
  service_account_id = var.service_account_id

  scheduling_policy {
    preemptible = true
  }

  resources {
    cores         = 2
    memory        = 8
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu_image.id
      size     = 30
    }
  }

  network_interface {
    subnet_id = var.subnet_id
    nat       = true
  }

  metadata = {
    ssh-keys           = "${var.instance_user}:${file(var.public_key_path)}"
    serial-port-enable = "1"
  }

  connection {
    type        = "ssh"
    user        = var.instance_user
    private_key = file(var.private_key_path)
    host        = self.network_interface.0.nat_ip_address
  }

  provisioner "file" {
    source      = "${path.module}/scripts/setup_mlflow.sh"
    destination = "/home/${var.instance_user}/setup_mlflow.sh"
  }

  provisioner "file" {
    content = templatefile("${path.module}/scripts/mlflow.conf.tpl", {
      s3_endpoint_url = var.s3_endpoint_url
      s3_bucket_name  = var.s3_bucket_name
      s3_access_key   = var.s3_access_key
      s3_secret_key   = var.s3_secret_key
      mlflow_port     = var.mlflow_port
    })
    destination = "/home/${var.instance_user}/mlflow.conf"
  }

  provisioner "file" {
    content = templatefile("${path.module}/scripts/mlflow.service.tpl", {
      s3_bucket_name = var.s3_bucket_name
      mlflow_port    = var.mlflow_port
    })
    destination = "/home/${var.instance_user}/mlflow.service"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/${var.instance_user}/setup_mlflow.sh",
      "/home/${var.instance_user}/setup_mlflow.sh"
    ]
  }
}
