terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.119.0"
    }
  }
  required_version = ">= 1.3.0"
}

resource "yandex_vpc_network" "main" {
  name      = "heart-api-network"
  folder_id = var.folder_id
}

resource "yandex_vpc_subnet" "main" {
  name           = "heart-api-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.main.id
  v4_cidr_blocks = [var.network_cidr]
  folder_id      = var.folder_id
}

resource "yandex_vpc_security_group" "k8s" {
  name       = "heart-api-k8s-sg"
  network_id = yandex_vpc_network.main.id
  folder_id  = var.folder_id

  ingress {
    protocol       = "TCP"
    description    = "Allow HTTP"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 80
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow HTTPS"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 443
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow API port"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 8000
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow Kubernetes API"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 6443
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow Kubernetes NodePort range"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 30000
    to_port        = 32767
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow SSH"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 22
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow MLflow tracking server"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 5000
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow Kafka SASL_SSL"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 9091
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow Kafka plaintext"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 9092
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow Grafana UI"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 3000
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow Prometheus UI"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 9090
  }

  ingress {
    protocol       = "TCP"
    description    = "Allow Airflow UI"
    v4_cidr_blocks = ["0.0.0.0/0"]
    port           = 8080
  }

  ingress {
    protocol       = "ANY"
    description    = "Allow YC load balancer health checks"
    v4_cidr_blocks = ["198.18.235.0/24", "198.18.248.0/24"]
    from_port      = 0
    to_port        = 65535
  }

  ingress {
    protocol       = "ANY"
    description    = "Allow internal traffic"
    v4_cidr_blocks = [var.network_cidr]
    from_port      = 0
    to_port        = 65535
  }

  egress {
    protocol       = "ANY"
    description    = "Allow outbound traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port      = 0
    to_port        = 65535
  }
}
