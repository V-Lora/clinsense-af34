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

## Log imutável para replay

O log imutável do pipeline é o object store (MinIO no Caminho B, S3 no Caminho A):
cada leitura fica como JSON cru particionado em year=/month=/day=/hour= e nunca é
reescrita. Se o algoritmo de detecção mudasse amanhã e precisasse recalcular seis
meses, a resposta seria uma nova varredura nesse prefixo — os dados originais
continuam intactos.

O DynamoDB Streams não serve para isso. Sua retenção máxima é de 24 horas, e a
tabela clinsense_quente apaga por TTL de 24 h por definição: é cache com prazo, não
arquivo. A tabela clinsense_alertas guarda 30 dias do resultado do detector —
também insuficiente para recalcular seis meses.

## Autoria e uso de IA

Usamos assistência de IA para levantar o esqueleto inicial do docker-compose.yml, o
boilerplate do handler da Lambda, a estrutura dos scripts de demonstração e a redação
inicial da Parte A do relatório. Revisamos manualmente e corrigimos: o handler
(guard contra a recursão do SNS, leitura de Records e chave patient_id+ts), o up.sh
(geração de senha por openssl rand e idempotência), o bridge.py (tolerância à ausência
do Firehose e invocação da Lambda) e o simulador (média e desvio do enunciado, janela
da anomalia). As decisões de arquitetura — AP/PACELC, escolha do buffer, divisão
quente/frio e o recorte da LGPD do oferente — são do grupo. As capturas e o screencast
foram produzidos por nós, com o ambiente rodando.

## Log imutável para replay

O object store particionado (`leituras/year=/month=/day=/hour=`) é o log imutável do pipeline.
Se o algoritmo de detecção mudasse e fosse preciso recalcular seis meses, basta reler os prefixos
por período com DuckDB e reprocessar. O DynamoDB Streams não serve para isso: retém 24 h, e a tabela
quente expira por TTL no mesmo prazo. O frio no MinIO é a única cópia que sobrevive à janela.
