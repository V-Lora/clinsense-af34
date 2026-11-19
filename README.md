# ClinSense — AF34 IoT e Big Data

Telemonitoramento de pacientes crônicos com pulseiras IoT. Projeto acadêmico da
disciplina Arquiteturas de Computação para IoT e Big Data (04803-80), turma 493-02AN.

## Personalização do grupo

| Dimensão | Escolha |
|---|---|
| Cidade da unidade | São Caetano do Sul |
| Oferente externo (A.3) | SaudePlan — operadora de plano de saúde |
| Paciente anômalo | P246 |
| Caminho | B — LocalStack + Docker Compose |

## Fluxo

    Pulseira (MQTT) -> Mosquitto -> bridge -> S3/MinIO    (frio, JSON cru particionado)
                                  -> Lambda detector -> DynamoDB quente (TTL 24h)
                                                     -> DynamoDB alertas (TTL 30d)
                                                     -> SNS (BPM > 120, BPM < 50 ou SpO2 < 92)

Duas pipelines paralelas: o frio é gravado pela bridge, o quente e o alerta pelo
detector. Não há log distribuído intermediário nem conversão para Parquet.

## Componentes

| Recurso | Nome |
|---|---|
| Object store (frio) | bucket `clinsense-raw`, prefixo `leituras/year=/month=/day=/hour=` |
| DynamoDB (quente) | `clinsense_quente`, TTL 24 h |
| DynamoDB (alertas) | `clinsense_alertas`, TTL 30 dias |
| Tópico SNS | `clinsense-alertas` |
| Função Lambda | `clinsense-processador` (Python 3.12) |
| Broker MQTT | Mosquitto, autenticação por usuário/senha gerada no `up.sh` |
| Tópico MQTT | `clinsense/pacientes/{patient_id}/telemetria` |

## Pré-requisitos

- Docker e Docker Compose
- Terraform >= 1.6
- Python 3 com `boto3` e `duckdb` (use `.venv`)

## Como subir

    ./scripts/up.sh
    cd infra && terraform apply -auto-approve

O `up.sh` é idempotente: gera `MQTT_PASSWORD` e `MINIO_ROOT_PASSWORD` com
`openssl rand` se estiverem vazios, escreve o `passwd` do Mosquitto e sobe os
três containers com as portas presas em 127.0.0.1.

## Como validar

    ./scripts/demo.sh 130      # simulador de 10 pulseiras por 130 s
    bash scripts/evidence.sh   # containers, tabelas, detector, object store e consulta analítica

A consulta analítica usa DuckDB sobre o JSON do object store, com `read_json_auto`.

## Como derrubar

    ./scripts/down.sh
    docker ps -aq --filter name=clinsense-localstack-lambda | xargs -r docker rm

O segundo comando remove os containers efêmeros que o LocalStack cria por
invocação de Lambda e que o `down.sh` não alcança.

## Decisões registradas

- `docs/ADR-001-pipeline.md` — escolha do Caminho B e do buffer gerenciado
- `docs/ADR-002-ingestao-mqtt.md` — ponte MQTT e gravação no data lake
- `docs/ADR-003-decisoes-locais.md` — decisões específicas do ambiente local

## Log imutável para replay

O object store é o log imutável do pipeline: cada leitura fica como JSON cru
particionado em `year=/month=/day=/hour=` e nunca é reescrita. Se o algoritmo de
detecção mudasse e precisasse recalcular seis meses, a resposta seria uma nova
varredura nesse prefixo — os dados originais continuam intactos.

O DynamoDB Streams não serve para isso. A retenção máxima é de 24 horas, e a tabela
`clinsense_quente` apaga por TTL de 24 h por definição: é cache com prazo, não
arquivo. A tabela `clinsense_alertas` guarda 30 dias do resultado do detector —
também insuficiente para recalcular seis meses.

## Limitação conhecida

O Firehose existe no LocalStack (a criação via API responde com ARN válido), mas o
provider Terraform recebe `UnrecognizedClientException` no `CreateDeliveryStream`.
Para não bloquear a entrega, a bridge assume a gravação e produz a mesma partição
`year=/month=/day=/hour=` diretamente no object store. O bloco Terraform está em
`infra/pipeline_firehose.tf.desativado` e na AWS real sobe sem alteração de código.

## Autoria e uso de IA

Ver `AUTORIA.md`, que declara as ferramentas utilizadas, os trechos apoiados e onde
houve revisão manual do grupo.
