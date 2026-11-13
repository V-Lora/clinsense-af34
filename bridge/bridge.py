#!/usr/bin/env python3
"""Ponte MQTT -> Firehose e espelho particionado no MinIO."""
import json
import os

import boto3
import paho.mqtt.client as mqtt

ENDPOINT = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
STREAM = os.getenv("FIREHOSE_STREAM", "clinsense-frio")
BUCKET = os.getenv("BUCKET_FRIO", "clinsense-raw")

HOST = os.getenv("MQTT_HOST", "127.0.0.1")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USER = os.getenv("MQTT_USER", "clinsense")
PWD = os.getenv("MQTT_PASSWORD", "")

MINIO_USER = os.getenv("MINIO_ROOT_USER", "")
MINIO_PWD = os.getenv("MINIO_ROOT_PASSWORD", "")

TOPICO = "clinsense/pacientes/+/telemetria"

kw = dict(endpoint_url=ENDPOINT, region_name="us-east-1",
          aws_access_key_id="test", aws_secret_access_key="test")
firehose = boto3.client("firehose", **kw)
lam = boto3.client("lambda", **kw)
FUNCAO = os.getenv("LAMBDA_DETECTOR", "clinsense-processador")

minio = boto3.client(
    "s3",
    endpoint_url="http://127.0.0.1:9000",
    region_name="us-east-1",
    aws_access_key_id=MINIO_USER,
    aws_secret_access_key=MINIO_PWD,
)

recebidas = 0
firehose_avisado = False


def particao(ts):
    d, h = ts[:10], ts[11:13]
    ano, mes, dia = d.split("-")
    return "leituras/year=%s/month=%s/day=%s/hour=%s" % (ano, mes, dia, h)


def ao_conectar(c, u, f, rc):
    if rc == 0:
        c.subscribe(TOPICO, qos=1)
        print("ponte conectada, assinando %s" % TOPICO, flush=True)
    else:
        print("falha MQTT rc=%s" % rc, flush=True)


def ao_receber(c, u, msg):
    global recebidas, firehose_avisado
    try:
        d = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        return

    linha = (json.dumps(d) + "\n").encode()

    try:
        firehose.put_record(DeliveryStreamName=STREAM, Record={"Data": linha})
    except Exception as e:
        if not firehose_avisado:
            print("firehose indisponivel (aviso unico): %s" % e, flush=True)
            firehose_avisado = True

    lam.invoke(FunctionName=FUNCAO, InvocationType="Event", Payload=linha)

    chave = "%s/%s-%s.json" % (
        particao(d.get("ts", "")), d.get("patient_id"), d.get("ts", "").replace(":", "")
    )
    minio.put_object(Bucket=BUCKET, Key=chave, Body=linha)

    recebidas += 1
    if recebidas % 10 == 0:
        print("[%d] %s bpm=%s spo2=%s" % (recebidas, d.get("patient_id"), d.get("bpm"), d.get("spo2")), flush=True)


def main():
    c = mqtt.Client(client_id="clinsense-bridge", protocol=mqtt.MQTTv311)
    c.username_pw_set(USER, PWD)
    c.on_connect = ao_conectar
    c.on_message = ao_receber
    c.connect(HOST, PORT, keepalive=30)
    print("ponte %s:%s -> Firehose %s + MinIO %s" % (HOST, PORT, STREAM, BUCKET), flush=True)
    c.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nponte encerrada, %d registros" % recebidas)
