module "network" {
  source = "./modules/network"

  folder_id    = var.yc_config.folder_id
  zone         = var.yc_config.zone
  network_cidr = var.network_cidr
}

module "iam" {
  source = "./modules/iam"

  folder_id            = var.yc_config.folder_id
  service_account_name = var.yc_service_account_name
}

module "storage" {
  source = "./modules/storage"

  folder_id   = var.yc_config.folder_id
  bucket_name = var.yc_bucket_name
  access_key  = module.iam.access_key
  secret_key  = module.iam.secret_key

  depends_on = [module.iam]
}

module "k8s" {
  source = "./modules/k8s"

  folder_id          = var.yc_config.folder_id
  zone               = var.yc_config.zone
  cluster_name       = var.cluster_name
  node_count         = var.node_count
  node_cores         = var.node_cores
  node_memory        = var.node_memory
  node_disk_size     = var.node_disk_size
  network_id         = module.network.network_id
  subnet_id          = module.network.subnet_id
  security_group_ids = [module.network.security_group_id]

  depends_on = [module.network]
}

module "kafka-cluster" {
  source = "./modules/kafka-cluster"

  cluster_name       = var.yc_kafka_cluster_name
  network_id         = module.network.network_id
  subnet_ids         = [module.network.subnet_id]
  security_group_ids = [module.network.security_group_id]
  zone               = var.yc_config.zone
  producer_password  = var.kafka_producer_password
  consumer_password  = var.kafka_consumer_password

  depends_on = [module.network]
}

module "mlflow-server" {
  source = "./modules/mlflow-server"

  instance_name       = var.yc_mlflow_instance_name
  service_account_id  = module.iam.service_account_id
  subnet_id           = module.network.subnet_id
  ubuntu_image_family = var.ubuntu_image_family
  public_key_path     = var.public_key_path
  private_key_path    = var.private_key_path
  s3_endpoint_url     = var.yc_storage_endpoint_url
  s3_bucket_name      = module.storage.bucket
  s3_access_key       = module.iam.access_key
  s3_secret_key       = module.iam.secret_key

  depends_on = [module.storage, module.iam, module.network]
}

resource "local_file" "variables_file" {
  content = jsonencode({
    YC_ZONE           = var.yc_config.zone
    YC_FOLDER_ID      = var.yc_config.folder_id
    YC_SUBNET_ID      = module.network.subnet_id
    YC_NETWORK_ID     = module.network.network_id
    YC_SSH_PUBLIC_KEY = trimspace(file(var.public_key_path))
    # S3
    S3_ENDPOINT_URL = var.yc_storage_endpoint_url
    S3_ACCESS_KEY   = module.iam.access_key
    S3_SECRET_KEY   = module.iam.secret_key
    S3_BUCKET_NAME  = module.storage.bucket
    # Kubernetes
    K8S_CLUSTER_ID   = module.k8s.cluster_id
    K8S_CLUSTER_NAME = module.k8s.cluster_name
    # MLflow
    MLFLOW_TRACKING_URI = module.mlflow-server.mlflow_tracking_uri
    MLFLOW_EXTERNAL_IP  = module.mlflow-server.external_ip_address
    MLFLOW_INTERNAL_IP  = module.mlflow-server.internal_ip_address
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = module.kafka-cluster.bootstrap_servers
    KAFKA_INPUT_TOPIC       = module.kafka-cluster.input_topic
    KAFKA_OUTPUT_TOPIC      = module.kafka-cluster.output_topic
    KAFKA_PRODUCER_USER     = module.kafka-cluster.producer_user
    KAFKA_PRODUCER_PASSWORD = module.kafka-cluster.producer_password
    KAFKA_CONSUMER_USER     = module.kafka-cluster.consumer_user
    KAFKA_CONSUMER_PASSWORD = module.kafka-cluster.consumer_password
    KAFKA_SECURITY_PROTOCOL = "SASL_SSL"
    KAFKA_SASL_MECHANISM    = "SCRAM-SHA-512"
    KAFKA_SSL_CA_PATH       = "/usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt"
  })
  filename        = "${path.module}/variables.json"
  file_permission = "0600"
}
