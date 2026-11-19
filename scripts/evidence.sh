#!/usr/bin/env bash
[ -f .venv/bin/activate ] && . .venv/bin/activate

echo "=== 0. personalizacao do grupo ==="
set -a; . ./.env; set +a
echo "    unidade : ${CIDADE_UNIDADE:-nao definida}"
echo "    oferente: ${OFERENTE_NOME:-nao definido}"
echo "    paciente: ${PACIENTE_ANOMALO:-nao definido}"
echo

set -u
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a

echo "===== 1. containers ====="
docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}'

echo
echo "===== 2. tabelas ====="
docker exec clinsense-localstack awslocal dynamodb list-tables 2>/dev/null \
  | tr -d ' ",[]' | grep clinsense

echo
echo "===== 3. detector ====="
python3 scripts/resumo_ddb.py

echo
echo "===== 4. object store ====="
python3 scripts/resumo_minio.py

echo
echo "===== 5. consulta analitica ====="
python3 analytics/consulta.py 2>&1 | tail -15
