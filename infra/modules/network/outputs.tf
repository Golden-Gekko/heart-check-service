output "network_id" {
  value = yandex_vpc_network.main.id
}

output "subnet_id" {
  value = yandex_vpc_subnet.main.id
}

output "security_group_id" {
  value = yandex_vpc_security_group.k8s.id
}

output "network_cidr" {
  value = var.network_cidr
}
