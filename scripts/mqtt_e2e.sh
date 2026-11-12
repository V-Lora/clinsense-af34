#!/usr/bin/env bash
set -u

TOPICO="${TOPICO:-clinsense/leituras}"
FUNCAO="${FUNCAO:-clinsense-processador}"
DISPOSITIVO="${DISPOSITIVO:-sensor-MQTT}"
TEMPERATURA="${TEMPERATURA:-11.2}"
SAIDA="/tmp/clinsense-mqtt.out"

rm -f "$SAIDA"

# assinante em background: sai apos 1 mensagem e descarrega o buffer ao encerrar
docker exec clinsense-mosquitto mosquitto_sub -t "$TOPICO" -C 1 -W 20 >"$SAIDA" 2>/dev/null &
SUB_PID=$!

sleep 2
echo "assistindo ${TOPICO}"

echo "publicando: ${DISPOSITIVO} ${TEMPERATURA}C"
docker exec clinsense-mosquitto mosquitto_pub \
  -t "$TOPICO" \
  -m "{\"device_id\":\"${DISPOSITIVO}\",\"temperatura\":${TEMPERATURA}}"

wait "$SUB_PID" 2>/dev/null

payload=$(tr -d '\r' < "$SAIDA")

if [ -z "$payload" ]; then
  echo "ERRO: o assinante nao recebeu nada"
  exit 1
fi

echo "recebido: ${payload}"

docker exec clinsense-localstack awslocal lambda invoke \
  --function-name "$FUNCAO" \
  --payload "$payload" \
  /tmp/mqtt.json >/dev/null 2>&1

echo "resposta da lambda:"
docker exec clinsense-localstack cat /tmp/mqtt.json 2>/dev/null
echo
