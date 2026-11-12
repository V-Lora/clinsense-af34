# ADR-001 — Pipeline Clinsense

## Decisões de infraestrutura local (nov/2026)

**MinIO removido.** As imagens `minio/minio` foram retiradas do Docker Hub em setembro de 2026, e o `quay.io/minio/minio` fechou os pulls anônimos em 24/09/2026. O armazenamento de objetos passou a ser provido pelo S3 do LocalStack, já presente no ambiente e compatível com a API AWS S3 usada pelo pipeline.

**Healthcheck do LocalStack ajustado.** O teste original usava `curl`, binário ausente na imagem atual. Substituído por `awslocal s3 ls`, com `start_period` de 60s para cobrir o tempo de inicialização do serviço.

**Permissão do arquivo de senhas do Mosquitto.** O arquivo `mosquitto/config/passwd` é criado com dono 1883 (UID do usuário `mosquitto`) e modo 640. O broker abandona o privilégio de root na inicialização, por isso não consegue ler um arquivo `root:root 600`.
