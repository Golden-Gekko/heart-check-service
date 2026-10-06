#!/bin/bash

function log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')]: $1"
}

path_to_user="/home/ubuntu"
path_to_venv="$path_to_user/venv"

log "Обновление пакетов"
sudo apt-get update

log "Установка необходимых пакетов"
sudo apt-get install -y python3-pip python3-venv

log "Настройка виртуального окружения Python"
mkdir -p $path_to_venv
python3 -m venv $path_to_venv
$path_to_venv/bin/pip install --upgrade pip
$path_to_venv/bin/pip install mlflow==2.17.2 boto3==1.37.16

log "Копирование конфигурационного файла"
cp $path_to_user/mlflow.conf $path_to_user/.mlflow.conf
chmod 600 $path_to_user/.mlflow.conf

log "Настройка systemd сервиса"
sudo cp mlflow.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable mlflow.service
sudo systemctl start mlflow.service

log "Установка MLflow завершена успешно"
