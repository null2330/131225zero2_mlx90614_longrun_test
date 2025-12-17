#!/usr/bin/env python3
# =========================================================
# Zero2 sensor MQTT publisher (retain enabled)
#   - HLK-LD6002 (raw bytes sampling)
#   - MLX90614   (ambient / object temperature)
#   - TF-Luna    (distance)
# =========================================================

import time
import json
import socket
from datetime import datetime

import paho.mqtt.client as mqtt

# --- MLX90614 ---
import board
import busio
import adafruit_mlx90614

# --- TF-Luna ---
import serial

# --- HLK-LD6002 ---
import serial as serial_ld6002


# =========================
# Basic settings
# =========================
MQTT_HOST = "192.168.8.124"   # Pi5 broker IP
MQTT_PORT = 1883

ZERO2_ID = socket.gethostname()
TOPIC = f"zero2/{ZERO2_ID}/sensor"

INTERVAL_SEC = 900      # normal publish interval
WINDOW_SEC   = 5        # keep short to reduce load (was 30)


# =========================
# Init MLX90614 (I2C)
# =========================
i2c = busio.I2C(board.SCL, board.SDA)
mlx = adafruit_mlx90614.MLX90614(i2c)


# =========================
# Init TF-Luna (UART)
# =========================
tf = serial.Serial(
    port="/dev/serial0",
    baudrate=115200,
    timeout=1
)


# =========================
# Init HLK-LD6002 (USB/UART)
# =========================
ld6002 = serial_ld6002.Serial(
    port="/dev/ttyUSB0",
    baudrate=1382400,
    timeout=0.05
)


# =========================
# MQTT
# =========================
client = mqtt.Client()
client.enable_logger()

print("[MQTT] connecting...")
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_start()
print("[MQTT] connected")


# =========================
# TF-Luna read
# =========================
def read_tf_luna():
    try:
        if tf.in_waiting >= 9:
            data = tf.read(9)
            if len(data) == 9 and data[0] == 0x59 and data[1] == 0x59:
                dist = data[2] + data[3] * 256
                signal = data[4] + data[5] * 256
                return True, dist, signal
    except Exception:
        pass
    return False, None, None


# =========================
# HLK-LD6002 read (light & human-friendly)
#   - collect short chunks for WINDOW_SEC
#   - store only non-zero samples (to avoid "all zeros" spam)
# =========================
def read_ld6002_light():
    bytes_total = 0
    chunks_total = 0
    chunks_nonzero = 0
    sample_hex = []

    start = time.time()
    while time.time() - start < WINDOW_SEC:
        try:
            n = ld6002.in_waiting
            if n <= 0:
                time.sleep(0.01)
                continue

            chunk = ld6002.read(min(n, 256))
            chunks_total += 1
            bytes_total += len(chunk)

            if chunk and any(b != 0x00 for b in chunk):
                chunks_nonzero += 1
                if len(sample_hex) < 10:
                    sample_hex.append(chunk.hex()[:120])

        except Exception:
            pass

    return {
        "bytes_total": bytes_total,
        "chunks_total": chunks_total,
        "chunks_nonzero": chunks_nonzero,
        "sample_hex": sample_hex
    }


# =========================
# Main loop
# =========================
while True:
    started_utc = datetime.utcnow().isoformat()

    # --- TF-Luna ---
    tf_ok, tf_dist, tf_signal = read_tf_luna()

    # --- MLX90614 ---
    try:
        ambient_c = float(mlx.ambient_temperature)
        object_c  = float(mlx.object_temperature)
        mlx_ok = True
    except Exception:
        ambient_c = None
        object_c  = None
        mlx_ok = False

    # --- HLK-LD6002 ---
    ld = read_ld6002_light()

    finished_utc = datetime.utcnow().isoformat()

    payload = {
        "meta": {
            "zero2_id": ZERO2_ID,
            "topic": TOPIC,
            "started_utc": started_utc,
            "finished_utc": finished_utc,
            "interval_sec": INTERVAL_SEC,
            "window_sec": WINDOW_SEC
        },
        "tf_luna": {
            "ok": tf_ok,
            "distance_cm": tf_dist,
            "signal": tf_signal
        },
        "mlx90614": {
            "ok": mlx_ok,
            "ambient_c": round(ambient_c, 2) if ambient_c is not None else None,
            "object_c": round(object_c, 2) if object_c is not None else None
        },
        "hlk_ld6002": ld
    }

    msg = json.dumps(payload)
    info = client.publish(TOPIC, msg, qos=0, retain=True)  # ★retain=True
    print(f"[PUBLISH] topic={TOPIC} bytes={len(msg)} rc={info.rc}")

    time.sleep(INTERVAL_SEC)
