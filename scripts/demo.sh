#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a

DURACAO=${1:-90}
mkdir -p logs

echo "[1] ambiente"
echo "    paciente anomalo: ${PACIENTE_ANOMALO:-AUSENTE}"
echo "    janela: ${ANOMALIA_INICIO:-?}s a $(( ${ANOMALIA_INICIO:-0} + ${ANOMALIA_DURACAO:-0} ))s"

[ -n "${PACIENTE_ANOMALO:-}" ] || { echo "ERRO: PACIENTE_ANOMALO vazio no .env"; exit 1; }

echo "[2] ponte em segundo plano"
python3 bridge/bridge.py > logs/bridge.log 2>&1 &
BRIDGE=$!
sleep 3

echo "[3] simulador por ${DURACAO}s"
timeout "$DURACAO" python3 simulator/simulador.py > logs/simulador.log 2>&1
echo "    simulador encerrado"

sleep 3
kill "$BRIDGE" 2>/dev/null || true
wait "$BRIDGE" 2>/dev/null || true

echo "[4] resumo"
echo "    inicio do simulador:"
head -2 logs/simulador.log | sed 's/^/      /'
echo "    alertas de anomalia emitidos: $(grep -c ANOMALIA logs/simulador.log)"
echo "    registros na ponte: $(grep -c 'bpm=' logs/bridge.log)"
echo "    ultimas linhas da ponte:"
tail -2 logs/bridge.log | sed 's/^/      /'
