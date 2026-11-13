#!/usr/bin/env python3
"""Resume as particoes no object store."""
import os
from collections import Counter

import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://127.0.0.1:9000",
    region_name="us-east-1",
    aws_access_key_id=os.environ["MINIO_ROOT_USER"],
    aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
)

paginator = s3.get_paginator("list_objects_v2")
chaves = [o["Key"] for p in paginator.paginate(Bucket="clinsense-raw") for o in p.get("Contents", [])]

print("total de objetos: %d" % len(chaves))
if not chaves:
    raise SystemExit(0)

particoes = Counter("/".join(k.split("/")[:5]) for k in chaves)
print("\nparticoes:")
for p, n in sorted(particoes.items()):
    print("   %s  ->  %d objetos" % (p, n))

print("\nprimeiras chaves:")
for k in chaves[:4]:
    print("   ", k)
