#!/usr/bin/env python3
"""Simulador das pulseiras ClinSense v2 - ESP32-S3 + MAX30102 (PPG: BPM e SpO2)."""
import json
import os
import random
import signal
import sys
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

ANOMALO = os.getenv("PACIENTE_ANOMALO", "P123")
TOTAL = int(os.getenv("TOTAL_PULSEIRAS", "10"))
INTERVALO = float(os.getenv("INTERVALO_SEGUNDOS", "5"))
T_INICIO = float(os.getenv("ANOMALIA_INICIO", "120"))
T_DURACAO = float(os.getenv("ANOMALIA_DURACAO", "180"))

HOST = os.getenv("MQTT_HOST", "127.0.0.1")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USER = os.getenv("MQTT_USER", "clinsense")
PWD = os.getenv("MQTT_PASSWORD", "")

parar = threading.Event()


def montar_pacientes():
    outros = [f"P{i:03d}" for i in range(1, TOTAL + 1) if f"P{i:03d}" != ANOMALO]
    return [ANOMALO] + outros[: TOTAL - 1]


def normal():
    bpm = max(55, min(105, random.gauss(75, 8)))
    spo2 = max(94, min(100, random.gauss(97, 1.5)))
    return round(bpm), round(spo2)


def anomalo():
    return round(random.uniform(121, 145)), round(random.uniform(85, 91))


def pulseira(cliente, patient_id):
    inicio = time.time()
    while not parar.is_set():
        decorrido = time.time() - inicio
        ativa = patient_id == ANOMALO and T_INICIO <= decorrido < T_INICIO + T_DURACAO

        bpm, spo2 = anomalo() if ativa else normal()

        payload = {
            "patient_id": patient_id,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "bpm": bpm,
            "spo2": spo2,
        }
        cliente.publish(
            f"clinsense/pacientes/{patient_id}/telemetria",
            json.dumps(payload),
            qos=1,
        )

        if ativa:
            print(f"[ANOMALIA] {patient_id} bpm={bpm} spo2={spo2}", flush=True)

        if parar.wait(INTERVALO):
            break


def main():
    pacientes = montar_pacientes()

    cliente = mqtt.Client(client_id="clinsense-simulador", protocol=mqtt.MQTTv311)
    cliente.username_pw_set(USER, PWD)
    cliente.connect(HOST, PORT, keepalive=30)
    cliente.loop_start()

    print(f"publicando {len(pacientes)} pulseiras a cada {INTERVALO:.0f}s")
    print(f"paciente anomalo: {ANOMALO} | janela: {T_INICIO:.0f}s a {T_INICIO + T_DURACAO:.0f}s")

    time.sleep(1)
    threads = [
        threading.Thread(target=pulseira, args=(cliente, pid), daemon=True)
        for pid in pacientes
    ]
    for t in threads:
        t.start()

    def encerrar(*_):
        parar.set()

    signal.signal(signal.SIGINT, encerrar)
    signal.signal(signal.SIGTERM, encerrar)

    while not parar.is_set():
        parar.wait(1)

    for t in threads:
        t.join(timeout=2)
    cliente.loop_stop()
    cliente.disconnect()
    print("simulador encerrado")


if __name__ == "__main__":
    sys.exit(main())
