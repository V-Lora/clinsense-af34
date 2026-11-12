import json
import os
import time
from decimal import Decimal

import boto3

REGIAO = os.environ.get("AWS_REGION", "us-east-1")
LIMITE = Decimal(os.environ.get("LIMITE_TEMPERATURA", "8.0"))
ENDPOINT = os.environ.get("AWS_ENDPOINT_URL")

conexao = {"region_name": REGIAO}
if ENDPOINT:
    conexao["endpoint_url"] = ENDPOINT

dynamodb = boto3.resource("dynamodb", **conexao)
tabela = dynamodb.Table(os.environ["TABLE"])
sns = boto3.client("sns", **conexao)


def lambda_handler(event, context):
    leitura = extrair_leitura(event)

    if "Records" in event:
        print(f"notificacao ignorada: {leitura.get('device_id')}")
        return {"statusCode": 200, "body": json.dumps({"ignorado": True})}

    device_id = leitura["device_id"]
    temperatura = Decimal(str(leitura["temperatura"]))
    timestamp = int(leitura.get("timestamp", time.time()))
    alerta = temperatura > LIMITE

    tabela.put_item(Item={
        "device_id": device_id,
        "timestamp": timestamp,
        "temperatura": temperatura,
        "alerta": alerta,
    })
    print(f"gravado: {device_id} {temperatura}C alerta={alerta}")

    if alerta:
        sns.publish(
            TopicArn=os.environ["SNS_TOPIC"],
            Subject=f"Alerta de temperatura: {device_id}",
            Message=json.dumps({
                "device_id": device_id,
                "temperatura": float(temperatura),
                "limite": float(LIMITE),
                "timestamp": timestamp,
            }),
        )
        print(f"alerta publicado: {device_id}")

    return {
        "statusCode": 200,
        "body": json.dumps({"gravado": True, "alerta": alerta, "device_id": device_id}),
    }


def extrair_leitura(event):
    if "Records" in event and event["Records"]:
        corpo = event["Records"][0]["Sns"]["Message"]
    elif "body" in event:
        corpo = event["body"]
    else:
        corpo = event

    dados = json.loads(corpo) if isinstance(corpo, str) else corpo

    if "device_id" not in dados or "temperatura" not in dados:
        raise ValueError("payload precisa conter device_id e temperatura")

    return dados
