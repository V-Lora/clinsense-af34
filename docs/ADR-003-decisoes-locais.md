> **Nota de revisão (13/11/2026):** o MinIO foi reintroduzido no compose no commit `5d01460` e opera em `127.0.0.1:9000`. A decisão de substituí-lo pelo S3 do LocalStack, registrada abaixo, foi revertida. O restante deste documento continua válido.

# ADR-003 — Decisões de infraestrutura local

## Decisões de infraestrutura local (nov/2026)

**MinIO removido.** As imagens `minio/minio` foram retiradas do Docker Hub em setembro de 2026, e o `quay.io/minio/minio` fechou os pulls anônimos em 24/09/2026. O armazenamento de objetos passou a ser provido pelo S3 do LocalStack, já presente no ambiente e compatível com a API AWS S3 usada pelo pipeline.

**Healthcheck do LocalStack ajustado.** O teste original usava `curl`, binário ausente na imagem atual. Substituído por `awslocal s3 ls`, com `start_period` de 60s para cobrir o tempo de inicialização do serviço.

**Permissão do arquivo de senhas do Mosquitto.** O arquivo `mosquitto/config/passwd` é criado com dono 1883 (UID do usuário `mosquitto`) e modo 640. O broker abandona o privilégio de root na inicialização, por isso não consegue ler um arquivo `root:root 600`.

## Provisionamento com Terraform (Fase 4)

**Bucket importado, nao recriado.** O bucket `clinsense-raw` ja existia desde a Fase 3. Foi incorporado ao state com `terraform import aws_s3_bucket.raw clinsense-raw`, evitando conflito de nome.

**Aplicacao em ciclos.** Na montagem inicial a politica IAM dependente do role e o trigger do SNS exigiram applies separados, porque o LocalStack pode falhar na propagacao de role dentro do mesmo apply (total 4 + 1 + 2 recursos). Em execucoes posteriores, com o ambiente estavel, os 7 recursos foram criados em um unico apply; quando o LocalStack perde o estado, um novo apply recria tudo de uma vez.

**Provider configurado para LocalStack.** Todas as chamadas sao redirecionadas para `http://localhost:4566`, com credenciais ficticias e validacao de conta desativada. O mesmo codigo serve para a AWS real trocando apenas o bloco `endpoints`.

**Integracao SNS para Lambda validada.** O teste publicou no topico e o log da funcao registrou um segundo RequestId, confirmando que a assinatura nao ficou em `PendingConfirmation`.

## Prevencao de recursao SNS para Lambda (Fase 5)

**Problema.** A funcao `clinsense-processador` publica alertas no topico `clinsense-alertas` e tambem esta inscrita nele. Cada publicacao reentregava o alerta para a propria funcao, que gravava e publicava novamente, gerando laco infinito. O defeito era invisivel na tabela DynamoDB: como o relay do SNS preserva o `timestamp`, a chave `device_id` + `timestamp` se repetia e o `put_item` sobrescrevia o registro anterior em vez de criar uma linha nova. O laco so podia ser detectado pelo log de execucao.

**Evidencia.** Uma unica invocacao do sensor-02 gerou nove RequestIds consecutivos em aproximadamente 300 ms, todos com `gravado` e `alerta publicado`, enquanto o `scan` permanecia com dois itens.

**Decisao.** O handler retorna imediatamente quando o evento contem `Records`, indicando invocacao originada do proprio topico. Nesse caminho a funcao registra `notificacao ignorada` e nao grava nem republica nada.

**Validacao.** Uma invocacao do sensor-03 produziu exatamente duas execucoes: `gravado` + `alerta publicado` (19,98 ms) e `notificacao ignorada` (1,84 ms), sem execucoes posteriores. O custo do descarte e cerca de dez vezes menor que o do processamento real.

**Alternativa considerada.** Separar o topico de ingestao do topico de notificacao eliminaria o laco por arquitetura. Foi descartada nesta entrega por exigir um segundo topico e uma nova assinatura, mantendo a solucao atual como suficiente para o escopo.
