# ClinSense - AF34 IoT e Big Data

Projeto academico de simulacao de telemetria de sensores.

## Caminho escolhido

Caminho B - execucao local com Docker, LocalStack e Mosquitto.

O README anterior citava MinIO como camada de objeto. O ambiente implementado
usa o S3 do LocalStack para o mesmo papel: o payload bruto de cada leitura fica
em s3://clinsense-raw/leituras/{device_id}/{timestamp}.json. O MinIO nao faz
parte da entrega.

Justificativa registrada em docs/ADR-001-pipeline.md.

## Fluxo

    MQTT (sensor) -> ponte -> Lambda -> S3 (payload bruto)
                                      -> DynamoDB (serie temporal)
                                      -> SNS (alerta quando temperatura > 8 C)

## Componentes

| Recurso         | Nome                 |
|-----------------|----------------------|
| Bucket S3       | clinsense-raw        |
| Tabela DynamoDB | clinsense-leituras   |
| Topico SNS      | clinsense-alertas    |
| Funcao Lambda   | clinsense-processador|
| Topico MQTT     | clinsense/leituras   |

## Pre-requisitos

- Docker e Docker Compose
- Terraform >= 1.6

## Como subir

    docker compose up -d
    sleep 75
    cd infra && terraform apply -auto-approve

O sleep e necessario: o LocalStack leva cerca de 60 segundos para aceitar
comandos, e o healthcheck do compose reflete isso.

## Como validar

    bash scripts/test-e2e.sh

## Como derrubar

    ./scripts/down.sh

## Decisoes registradas

- docs/ADR-001-pipeline.md - provisionamento e prevencao de recursao SNS
- docs/ADR-002-ingestao-mqtt.md - ponte MQTT e gravacao no data lake
- docs/STATUS.md - estado atual da entrega

## Limitacao conhecida

O ambiente nao e reproduzivel de forma automatica. Ao reiniciar os containers,
o DynamoDB preserva o estado mas S3, Lambda, SNS e IAM se perdem e exigem
terraform apply. O bucket volta vazio, entao registros antigos da tabela ficam
sem objeto correspondente e devem ser removidos manualmente.
