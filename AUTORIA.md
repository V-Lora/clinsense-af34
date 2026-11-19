# AUTORIA — AF34 ClinSense

## Ferramentas de IA utilizadas

- Assistente de IA conversacional — apoio na depuração do pipeline e na redação da Parte A.
- Geração de código assistida — esqueleto de trechos do Terraform e dos scripts de evidência.

## Onde a IA foi usada

| Trecho | Uso | Revisão humana |
|---|---|---|
| `infra/*.tf` | Esqueleto inicial dos recursos (S3, DynamoDB, Lambda, SNS, IAM) | Revisado recurso por recurso; `terraform state list` confere os 12 recursos |
| `scripts/evidence.sh` | Estrutura do script de evidências | Corrigido: guarda de `.venv` e bloco de personalização do grupo |
| `simulator/simulador.py` | Apoio na função `anomalo()` e no loop `pulseira()` | Janela 120–300 s e faixa 121–145 / 85–91 definidas e testadas pelo grupo |
| `bridge/bridge.py` | Apoio na ponte Mosquitto → Firehose | Corrigido para aceitar `MQTT_PASSWORD` e `MQTT_PASS` |
| `infra/lambda/handler.py` | Apoio na lógica do detector | Regra dos três limiares e destino SNS revisados linha a linha |
| `AF34_PARTE_A.docx` | Apoio de redação em A.1, A.2 e A.3 | Argumento do § 5º e enquadramento do SaudePlan definidos pelo grupo |

## Decisões tomadas sem apoio de IA

- Escolha do Caminho B por ausência de cartão internacional no grupo.
- Tupla de personalização: São Caetano do Sul × SaudePlan × P246.
- Buffer gerenciado em vez de log distribuído, e desenho dual-write que dispensa job de promoção entre quente e frio.
- Estratégia jurídica da A.3: atacar o Art. 11 § 5º antes do Art. 12, para resolver o caso sem depender da discussão de anonimização.

## Declaração

Nenhum código deste repositório foi copiado de outro grupo ou de tutorial sem adaptação. As decisões arquiteturais e jurídicas são do grupo. Assumimos a responsabilidade pelo conteúdo integral da entrega, inclusive pelos trechos apoiados por IA.
