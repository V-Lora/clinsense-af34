# ADR-001 — Caminho B e por que buffer JSON + NoSQL quente

**Status:** aceito · **Data:** 2026-11-13 · **AF34 ClinSense**

## Contexto

A ClinSense ingere 40 pulseiras (10 no lab) a uma leitura a cada 5 s, precisa emitir
alerta em menos de 30 s, reter 24 meses de telemetria crua para auditoria e permitir
consulta analítica ad-hoc sem competir com a ingestão. Nenhum integrante do grupo
possui cartão internacional, o que elimina o Caminho A na prática.

## Decisão

**1. Caminho B (LocalStack + Docker Compose).** Mesma rubrica, risco financeiro zero.
O mesmo Terraform serve à AWS real trocando apenas o bloco `endpoints`.

**2. Buffer gerenciado (Firehose), não Kafka nem Kinesis Streams.** Para 8 leituras
por segundo, o custo fixo decide: KDS cobra shard-hora 24/7 e MSK cobra broker-hora
com mínimo de dois brokers. O Firehose cobra por GB ingerido e dispensa consumidor
próprio. Abrimos mão do replay porque o object store já é o log.

**3. JSON cru particionado, não Parquet.** A conversão colunar adicionaria um estágio
que falha e um esquema a versionar, com ganho marginal em 640 objetos de teste. O
`read_json_auto` do DuckDB lê direto do object store e responde por paciente sem ETL.

**4. Sem cluster Kafka.** Três brokers, coordinator e retenção configurada são
infraestrutura acima do escopo de 48 leituras por minuto.

## Consequências

**Custo.** Zero no Caminho B. No Caminho A seria de centavos no Free Tier, mas exigiria
Billing Alarm e Budget como GATE.

**Ausência de Free Tier em KDS e Timestream.** Nenhum dos dois oferece camada gratuita,
o que os elimina para um trabalho de orçamento zero. Timestream também seria inadequado
por ser série temporal gerenciada com custo por GB-mês.

**Lock-in.** O GCP IoT Core foi descontinuado em 2023, encerrando a camada de ingestão
que muitos projetos assumiam como permanente. Por isso a ingestão fica em MQTT padrão
OASIS sobre Mosquitto, que roda em qualquer nuvem ou on-premise. A única dependência
proprietária é a API de destino, isolada atrás de uma bridge Python curta e
substituível sem tocar no simulador.

**Limitação aceita: Firehose no LocalStack.** O serviço responde
(`list-delivery-streams` retorna normalmente), mas a criação via provider Terraform
falha com `UnrecognizedClientException`. A bridge assume a gravação e produz a mesma
partição `year=/month=/day=/hour=` no object store; o bloco Terraform correspondente
está em `pipeline_firehose.tf.desativado`, com o motivo registrado. Na AWS real o
recurso é criado sem alteração de código.

**Reprocessamento.** O object store é o log imutável: mudar o limiar do detector
significa reler o histórico e recalcular, sem depender da retenção de 24 h do
DynamoDB Streams.
