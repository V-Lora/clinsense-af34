#!/usr/bin/env python3
"""Consulta analitica com DuckDB sobre o JSON cru no MinIO."""
import os
from pathlib import Path

import duckdb

env = {}
for ln in Path(".env").read_text().splitlines():
    if "=" in ln and not ln.lstrip().startswith("#"):
        k, v = ln.split("=", 1)
        env[k.strip()] = v.strip()

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("SET s3_endpoint='127.0.0.1:9000';")
con.execute("SET s3_use_ssl=false;")
con.execute("SET s3_url_style='path';")
con.execute("SET s3_access_key_id='%s';" % env["MINIO_ROOT_USER"])
con.execute("SET s3_secret_access_key='%s';" % env["MINIO_ROOT_PASSWORD"])

sql = """
SELECT patient_id,
       count(*)            AS leituras,
       round(avg(bpm), 1)  AS bpm_medio,
       round(avg(spo2), 1) AS spo2_medio
FROM read_json_auto('s3://clinsense-raw/leituras/**/*.json')
GROUP BY patient_id
ORDER BY patient_id
"""

res = con.execute(sql)
colunas = [d[0] for d in res.description]
linhas = res.fetchall()

larg = [max(len(str(c)), *(len(str(r[i])) for r in linhas)) if linhas else len(str(c))
        for i, c in enumerate(colunas)]

print("  ".join(str(c).ljust(larg[i]) for i, c in enumerate(colunas)))
print("  ".join("-" * l for l in larg))
for r in linhas:
    print("  ".join(str(v).ljust(larg[i]) for i, v in enumerate(r)))

print()
print("total de pacientes: %d" % len(linhas))
