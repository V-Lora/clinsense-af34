# ClinSense - Status da entrega parcial

Data: 13/11/2026

## Fluxo implementado

MQTT (sensor) -> Ponte -> Lambda -> S3 (payload bruto)
                                 -> DynamoDB (serie temporal)
                                 -> SNS (alerta quando temperatura > 8 C)

## Validado com evidencia

- Infraestrutura: 7 recursos criados por Terraform, apply em ciclo unico
- Handler: grava no DynamoDB e no S3; retorna gravado=true
- Limite de temperatura: 5.0 C gera alerta=false, 10.5 C gera alerta=true
- Guarda anti-recursao: notificacao do SNS descartada em cerca de 1,4 ms
- Ponte MQTT: leitura publicada no topico chega ao DynamoDB e ao S3
- Data lake: objeto JSON com o payload original, sem envelope do SNS
- Proporcao: 3 itens no DynamoDB para 3 objetos no S3
- Custos: cerca de 26 ms com S3 contra 20 ms sem, acrescimo de 6 ms

## Limitacao conhecida

O ambiente nao e reproduzivel de forma automatica. Apos reiniciar os
containers, o DynamoDB preserva o estado mas S3, Lambda, SNS e IAM sao
perdidos, exigindo terraform apply para reconciliar. O bucket volta vazio,
entao registros antigos da tabela ficam sem objeto correspondente e devem
ser removidos manualmente.

## Pendencias

- README desatualizado: menciona MinIO, ausente no ambiente
- ADR-001 linha 15 afirma tres ciclos de apply, contrariado pela execucao atual
- scripts/test-e2e.sh nao existe
- Definir o dominio: pulseira medica ou cadeia de frio de medicamentos
- bind mount .localstack provoca Permission denied no host sem sudo

## Commits

bc70c5d Fase 4 infraestrutura
a6bf610 Fase 5 handler e guarda anti-recursao
3617e77 Fase 6 ponte MQTT
559e385 Fase 7 gravacao no S3
baa8b96 ADR-002 com a decisao do data lake
4205d97 Mosquitto consolidado no compose
5440ad5 remocao do compose duplicado
b35bfd2 persistencia do LocalStack ativada
