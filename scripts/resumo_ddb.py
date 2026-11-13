#!/usr/bin/env python3
"""Resume as tabelas do detector: totais e amostras legiveis."""
import boto3

kw = dict(endpoint_url="http://localhost:4566", region_name="us-east-1",
          aws_access_key_id="test", aws_secret_access_key="test")
ddb = boto3.client("dynamodb", **kw)


def total(tabela):
    return ddb.scan(TableName=tabela, Select="COUNT")["Count"]


def amostra(tabela, limite=4):
    r = ddb.scan(TableName=tabela, Limit=limite)
    for item in r.get("Items", []):
        print("   ", {k: list(v.values())[0] for k, v in item.items() if k != "ttl"})


print("clinsense_quente: %d registros" % total("clinsense_quente"))
amostra("clinsense_quente", 3)

print()
print("clinsense_alertas: %d registros" % total("clinsense_alertas"))
amostra("clinsense_alertas", 4)

print()
r = ddb.scan(
    TableName="clinsense_alertas",
    FilterExpression="patient_id = :p",
    ExpressionAttributeValues={":p": {"S": "P246"}},
    Select="COUNT",
)
print("alertas do paciente anomalo P246: %d" % r["Count"])
