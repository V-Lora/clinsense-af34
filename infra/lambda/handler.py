import os
import json


def lambda_handler(event, context):
    print("Evento recebido:", json.dumps(event))
    return {
        "statusCode": 200,
        "body": json.dumps({
            "bucket": os.environ.get("BUCKET"),
            "table": os.environ.get("TABLE"),
            "ok": True,
        }),
    }
