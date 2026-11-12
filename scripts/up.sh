#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  echo "[up] .env existente, reaproveitando segredos"
else
  echo "[up] gerando segredos novos"
  {
    echo "MQTT_USER=clinsense"
    echo "MQTT_PASS=$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | cut -c1-24)"
    echo "MINIO_ROOT_USER=clinsense$(openssl rand -hex 3)"
    echo "MINIO_ROOT_PASSWORD=$(openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | cut -c1-28)"
    echo "LOCALSTACK_AUTH_TOKEN=${LOCALSTACK_AUTH_TOKEN:-}"
  } > .env
  chmod 600 .env
fi

set -a; . ./.env; set +a

if [ -z "${LOCALSTACK_AUTH_TOKEN}" ]; then
  echo "[up] ERRO: LOCALSTACK_AUTH_TOKEN vazio." >&2
  echo "[up] exporte o token antes de rodar." >&2
  exit 1
fi

mkdir -p mosquitto/config mosquitto/data minio-data .localstack

cat > mosquitto/config/mosquitto.conf <<'CONF'
listener 1883
allow_anonymous false
password_file /mosquitto/config/passwd
persistence true
persistence_location /mosquitto/data/
log_dest stdout
CONF

if [ ! -f mosquitto/config/passwd ]; then
  docker run --rm -v "$PWD/mosquitto/config:/cfg" eclipse-mosquitto:2 \
    mosquitto_passwd -b -c /cfg/passwd "$MQTT_USER" "$MQTT_PASS"
  echo "[up] password file criado"
else
  echo "[up] password file mantido"
fi

docker compose up -d --wait
docker compose ps
