# ClinSense - Status da entrega parcial

Data: 12/11/2026

## Fluxo implementado

MQTT (sensor) -> Ponte -> Lambda -> S3 (payload bruto)
                                 -> DynamoDB (serie temporal)
                                 -> SNS (alerta quando temperatura > limite)

## Validado com evidencia

- Infraestrutura: 8 recursos criados por Terraform, apply em ciclo unico
- Handler: grava no DynamoDB e no S3, publica no SNS acima de 8 C
- Guarda anti-recursao: notificacao do SNS descartada em 1,36 ms
- Ponte MQTT: leitura publicada no topico chega ao DynamoDB
- Data lake: objeto JSON com o payload original, sem envelope do SNS
- Proporcao: 3 itens no DynamoDB para 3 objetos no S3
- Custos: 26,18 ms com S3 contra 19,98 ms sem, acrescimo de cerca de 6 ms

## Limitacao conhecida

Apos reinicializacao do ambiente com persistencia ativada, o DynamoDB
preservou o estado mas as invocacoes nao gravaram e o bucket nao foi
listado. A recuperacao exige terraform apply apos o restart. O ambiente
nao e reproduzivel de forma automatica ainda.

## Pendencias

- README desatualizado (menciona MinIO, ausente no ambiente)
- ADR-001 linha 15 afirma tres ciclos de apply,contrariado pela execucao atual
- scripts/test-e2e.sh nao existe
- Definir o dominio: pulseira medica ou cadeia de frio de medicamentos

## Commits

bc70c5d Fase 4 infraestrutura
a6bf610 Fase 5 handler e guarda anti-recursao
3617e77 Fase 6 ponte MQTT
559e385 Fase 7 gravacao no S3
baa8b96 ADR-002 com a decisao do data lake
4205d97 Mosquitto consolidado no compose
5440ad5 remocao do compose duplicado
b35bfd2 persistencia do LocalStack ativada
