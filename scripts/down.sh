#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose down -v --remove-orphans
echo "--- containers ---"
docker ps
echo "--- volumes ---"
docker volume ls
