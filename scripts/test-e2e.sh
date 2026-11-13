#!/usr/bin/env bash
set -u

FUNCAO="${FUNCAO:-clinsense-processador}"
TABELA="${TABELA:-clinsense-leituras}"
BUCKET="${BUCKET:-clinsense-raw}"
FALHAS=0

aws_() { docker exec clinsense-localstack awslocal "$@" 2>/dev/null; }
ok()   { echo "  [ok]    $1"; }
erro() { echo "  [FALHA] $1"; FALHAS=$((FALHAS + 1)); }

echo "== 1/5 limpando DynamoDB =="
aws_ dynamodb scan --table-name "$TABELA" \
  --query "Items[].[device_id.S,timestamp.N]" --output text 2>/dev/null \
| while read -r dev ts; do
    [ -z "${dev:-}" ] && continue
    aws_ dynamodb delete-item --table-name "$TABELA" \
      --key "{\"device_id\":{\"S\":\"$dev\"},\"timestamp\":{\"N\":\"$ts\"}}" >/dev/null
  done

echo "== 2/5 limpando S3 =="
aws_ s3 ls "s3://$BUCKET/leituras/" --recursive 2>/dev/null | awk '{print $4}' \
| while read -r chave; do
    [ -z "${chave:-}" ] && continue
    aws_ s3 rm "s3://$BUCKET/$chave" >/dev/null
  done

echo "== 3/5 invocando os dois ramos diretos =="
aws_ lambda invoke --function-name "$FUNCAO" \
  --payload '{"device_id":"sensor-A","temperatura":5.0}' /tmp/a.json >/dev/null
aws_ lambda invoke --function-name "$FUNCAO" \
  --payload '{"device_id":"sensor-B","temperatura":10.5}' /tmp/b.json >/dev/null

sa=$(aws_ cat /tmp/a.json 2>/dev/null)
sb=$(aws_ cat /tmp/b.json 2>/dev/null)

case "$sa" in
  *'"alerta": false'*) ok "sensor-A gravado com alerta=false" ;;
  *) erro "sensor-A inesperado: $sa" ;;
esac

case "$sb" in
  *'"alerta": true'*) ok "sensor-B gravado com alerta=true" ;;
  *) erro "sensor-B inesperado: $sb" ;;
esac

echo "== 4/5 invocando pela ponte MQTT =="
if bash scripts/mqtt_e2e.sh >/tmp/mqtt.out 2>&1; then
  grep -q '"gravado": true' /tmp/mqtt.out \
    && ok "sensor-MQTT gravado via MQTT" \
    || erro "ponte rodou mas a Lambda nao confirmou gravacao"
else
  erro "ponte MQTT falhou - veja /tmp/mqtt.out"
fi

echo "== 5/5 conferindo proporcao entre as camadas =="
itens=$(aws_ dynamodb scan --table-name "$TABELA" --query Count --output text 2>/dev/null)
objetos=$(aws_ s3 ls "s3://$BUCKET/leituras/" --recursive 2>/dev/null | grep -c '\.json')

echo "  DynamoDB: $itens itens"
echo "  S3:       $objetos objetos"

[ "$itens" = "3" ] && ok "3 itens na tabela" || erro "esperado 3 itens, encontrado $itens"
[ "$objetos" = "3" ] && ok "3 objetos no bucket" || erro "esperado 3 objetos, encontrado $objetos"

echo
if [ "$FALHAS" -eq 0 ]; then
  echo "RESULTADO: tudo ok"
  exit 0
fi
echo "RESULTADO: $FALHAS verificacao(oes) falharam"
exit 1
