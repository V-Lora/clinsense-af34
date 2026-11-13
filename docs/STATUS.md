# ClinSense - Status da entrega parcial

Data: 13/11/2026

## Fluxo implementado

MQTT (sensor) -> Ponte -> Lambda -> S3 (payload bruto)
                                 -> DynamoDB (serie temporal)
                                 -> SNS (alerta quando temperatura > 8 C)

## Validado com evidencia

- Infraestrutura: 7 recursos criados por Terraform, apply em ciclo unico,
  confirmado por `No changes` em execucao posterior
- Handler: grava no DynamoDB e no S3; retorna gravado=true
- Regra de alerta: 5.0 C gera alerta=false; 10.5 C gera alerta=true
- Guarda anti-recursao: notificacao do SNS descartada em cerca de 1,4 ms
- Ponte MQTT: leitura publicada no topico chega ao DynamoDB e ao S3
- Data lake: objeto JSON com o payload original, sem envelope do SNS
- Proporcao: 3 itens no DynamoDB para 3 objetos no S3
- Custos: cerca de 26 ms com S3 contra 20 ms sem, acrescimo de 6 ms
- Validacao automatizada: scripts/test-e2e.sh executa 5 verificacoes e
  encerra com "RESULTADO: tudo ok"

## Como reproduzir

    docker compose up -d
    sleep 75
    cd infra && terraform apply -auto-approve
    cd .. && bash scripts/test-e2e.sh

O sleep e necessario: o LocalStack leva cerca de 60 segundos para aceitar
comandos apos o start.

## Limitacoes conhecidas

1. O ambiente nao e reproduzivel de forma automatica. Apos reiniciar os
   containers, o DynamoDB preserva o estado mas S3, Lambda, SNS e IAM sao
   perdidos e exigem terraform apply. O bucket volta vazio, entao registros
   antigos da tabela ficam sem objeto correspondente.

2. O bind mount ./.localstack grava arquivos como root, impedindo limpeza
   pelo usuario do host sem sudo. A correcao planejada e trocar por volume
   nomeado, ainda nao aplicada.

3. O dominio fisico do projeto nao esta fechado: o README fala em pulseiras
   medicas, mas o limite de 8 C sugere cadeia de frio de medicamentos. A
   nomenclatura precisa ser alinhada entre README, handler e ADRs.

## Documentos

- docs/ADR-001-pipeline.md - provisionamento e prevencao de recursao SNS
- docs/ADR-002-ingestao-mqtt.md - ponte MQTT e gravacao no data lake
- README.md - fluxo, componentes e como subir

## Commits

bc70c5d Fase 4 infraestrutura
a6bf610 Fase 5 handler e guarda anti-recursao
3617e77 Fase 6 ponte MQTT
559e385 Fase 7 gravacao no S3
baa8b96 ADR-002 com a decisao do data lake
4205d97 Mosquitto consolidado no compose
5440ad5 remocao do compose duplicado
b35bfd2 persistencia do LocalStack ativada
8e0656b status inicial da entrega
744ecd3 status consolidado da entrega
14f0fe8 README e ADR-001 alinhados, teste e2e criado
c90f6a5 correcao do teste e2e
b91bfb7 filtro de objetos json na limpeza do S3
