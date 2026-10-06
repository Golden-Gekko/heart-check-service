output "service_account_id" {
  value = yandex_iam_service_account.main.id
}

output "access_key" {
  value = yandex_iam_service_account_static_access_key.main.access_key
}

output "secret_key" {
  value     = yandex_iam_service_account_static_access_key.main.secret_key
  sensitive = true
}
