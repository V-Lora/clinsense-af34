# ADR-002: Ponte de ingestao MQTT para Lambda

## Contexto

O pipeline exige ingestao de leituras de sensores via MQTT, mas o broker Mosquitto e o LocalStack rodam em containers isolados. Uma mensagem publicada no topico `clinsense/leituras` nao alcanca a funcao `clinsense-processador` sem um elemento de ligacao.

## Decisao

Ponte em shell (`scripts/mqtt_e2e.sh`) que assina o topico, publica a leitura de teste e invoca a Lambda com o payload recebido. A ponte usa `mosquitto_sub -C 1 -W 20` gravando em arquivo, nao em FIFO.

## Justificativa

O `paho-mqtt` nao esta disponivel no ambiente (sem `pip`, sem permissao de `sudo` para instalar pacotes). O `mosquitto_sub` ja existe dentro do container e elimina a dependencia externa.

O FIFO foi descartado apos teste: sem `-C 1`, o `mosquitto_sub` mantem o processo vivo e bufferiza a saida, entao o `read` nunca recebe dados. Com `-C 1`, o processo encerra ao receber a mensagem e descarrega o buffer no fechamento. Gravacao em arquivo comum e necessaria; pipe nao funciona.

## Configuracao do broker

O Mosquitto 2.x traz `allow_anonymous false` por padrao, recusando conexoes com `Connection Refused: not authorised`. A correcao foi montar `infra/mosquitto/mosquitto.conf` com `allow_anonymous true` via `docker-compose.mqtt.yml`.

O `docker cp` nao funciona nesse cenario: o diretorio `/mosquitto/config` e montado como somente leitura. A configuracao precisa vir do host.

## Validacao

Publish de `sensor-MQTT` com 11,2 C produziu:

- ponte: `recebido:` com o JSON e `resposta da lambda:` com statusCode 200
- DynamoDB: item `sensor-MQTT` com `alerta: true` e `timestamp` 1794513954
- tabela: 3 itens (`sensor-A`, `sensor-B`, `sensor-MQTT`)

## Limitacoes

A ponte roda sob demanda, nao como servico persistente. Para operacao continua seria necessario um listener em background ou integracao nativa do LocalStack com MQTT.

## Gravacao do payload bruto no data lake (Fase 7)

**Decisao.** O handler grava cada leitura no bucket `clinsense-raw`, na chave `leituras/{device_id}/{timestamp}.json`, antes de escrever no DynamoDB.

**Ordem das operacoes.** O `put_object` vem depois da guarda de `Records`. A notificacao devolvida pelo SNS nao grava no S3, evitando duplicidade no data lake — o mesmo motivo que levou a guarda a existir para o DynamoDB.

**Tolerancia a falha.** A chamada ao S3 esta envolvida em `try/except`. Uma indisponibilidade do data lake registra o erro no log mas nao descarta a leitura: o `put_item` no DynamoDB continua acontecendo. A ingestao tem prioridade sobre a camada analitica.

**Configuracao.** Nenhuma alteracao no Terraform foi necessaria: a variavel `BUCKET` ja estava injetada no ambiente da funcao e a politica IAM ja concedia `s3:PutObject`.

**Validacao.** Apos o deploy, a leitura de `sensor-MQTT` com 11,2 C produziu o objeto `leituras/sensor-MQTT/1794514287.json` com 49 bytes contendo o payload original, e o registro correspondente no DynamoDB com `alerta: true`.
