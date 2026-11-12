# ADR-001 — Pipeline Clinsense

## Decisões de infraestrutura local (nov/2026)

**MinIO removido.** As imagens `minio/minio` foram retiradas do Docker Hub em setembro de 2026, e o `quay.io/minio/minio` fechou os pulls anônimos em 24/09/2026. O armazenamento de objetos passou a ser provido pelo S3 do LocalStack, já presente no ambiente e compatível com a API AWS S3 usada pelo pipeline.

**Healthcheck do LocalStack ajustado.** O teste original usava `curl`, binário ausente na imagem atual. Substituído por `awslocal s3 ls`, com `start_period` de 60s para cobrir o tempo de inicialização do serviço.

**Permissão do arquivo de senhas do Mosquitto.** O arquivo `mosquitto/config/passwd` é criado com dono 1883 (UID do usuário `mosquitto`) e modo 640. O broker abandona o privilégio de root na inicialização, por isso não consegue ler um arquivo `root:root 600`.

## Provisionamento com Terraform (Fase 4)

**Bucket importado, nao recriado.** O bucket `clinsense-raw` ja existia desde a Fase 3. Foi incorporado ao state com `terraform import aws_s3_bucket.raw clinsense-raw`, evitando conflito de nome.

**Aplicacao em tres ciclos.** A politica IAM dependente do role e o trigger do SNS so foram aplicados depois que a base existia, porque o LocalStack falha na propagacao de role dentro do mesmo apply. Total: 4 + 1 + 2 recursos.

**Provider configurado para LocalStack.** Todas as chamadas sao redirecionadas para `http://localhost:4566`, com credenciais ficticias e validacao de conta desativada. O mesmo codigo serve para a AWS real trocando apenas o bloco `endpoints`.

**Integracao SNS para Lambda validada.** O teste publicou no topico e o log da funcao registrou um segundo RequestId, confirmando que a assinatura nao ficou em `PendingConfirmation`.
