"""Detector ClinSense - grava no quente, avalia limiares e alerta via SNS."""
import json
import os
import time
from datetime import datetime, timezone

import boto3

TABELA_QUENTE = os.getenv("TABELA_QUENTE", "clinsense_quente")
TABELA_ALERTAS = os.getenv("TABELA_ALERTAS", "clinsense_alertas")
TOPICO_SNS = os.getenv("TOPICO_SNS", "")

BPM_MAX = int(os.getenv("BPM_MAX", "120"))
BPM_MIN = int(os.getenv("BPM_MIN", "50"))
SPO2_MIN = int(os.getenv("SPO2_MIN", "92"))

ddb = boto3.resource("dynamodb")
sns = boto3.client("sns")


def lambda_handler(event, context):
    leitura = event

    if isinstance(event, dict) and "detail" in event:
        leitura = event["detail"]

    if isinstance(event, dict) and "Records" in event:
        reg = event["Records"][0]
        if reg.get("EventSource") == "aws:sns":
            print(json.dumps({"ignorado": "notificacao do proprio SNS"}))
            return {"statusCode": 200, "body": "{}"}
        corpo = reg.get("Sns", {}).get("Message") or reg.get("body", "{}")
        leitura = json.loads(corpo) if isinstance(corpo, str) else corpo

    patient_id = leitura.get("patient_id")
    if not patient_id:
        print(json.dumps({"erro": "payload sem patient_id", "recebido": str(leitura)}))
        return {"statusCode": 400, "body": "{}"}

    bpm = int(leitura.get("bpm", 0))
    spo2 = int(leitura.get("spo2", 0))
    ts = leitura.get("ts") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    agora = int(time.time())

    ddb.Table(TABELA_QUENTE).put_item(
        Item={
            "patient_id": patient_id,
            "ts": ts,
            "bpm": bpm,
            "spo2": spo2,
            "ttl": agora + 24 * 3600,
        }
    )

    motivos = []
    if bpm > BPM_MAX:
        motivos.append("bpm %d acima de %d" % (bpm, BPM_MAX))
    if bpm < BPM_MIN:
        motivos.append("bpm %d abaixo de %d" % (bpm, BPM_MIN))
    if spo2 < SPO2_MIN:
        motivos.append("spo2 %d abaixo de %d" % (spo2, SPO2_MIN))

    if not motivos:
        print(json.dumps({"patient_id": patient_id, "bpm": bpm, "spo2": spo2, "alerta": False}))
        return {"statusCode": 200, "body": json.dumps({"grava­do": True, "alerta": False})}

    texto = "; ".join(motivos)

    ddb.Table(TABELA_ALERTAS).put_item(
        Item={
            "patient_id": patient_id,
            "ts": ts,
            "bpm": bpm,
            "spo2": spo2,
            "motivo": texto,
            "ttl": agora + 30 * 24 * 3600,
        }
    )

    if TOPICO_SNS:
        sns.publish(
            TopicArn=TOPICO_SNS,
            Subject="ClinSense alerta %s" % patient_id,
            Message=json.dumps(
                {"patient_id": patient_id, "ts": ts, "bpm": bpm, "spo2": spo2, "motivo": texto}
            ),
        )

    print(json.dumps({"ALERTA": True, "patient_id": patient_id, "bpm": bpm, "spo2": spo2, "motivo": texto}))
    return {"statusCode": 200, "body": json.dumps({"gravado": True, "alerta": True})}
