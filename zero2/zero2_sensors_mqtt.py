#!/usr/bin/env python3
# ============================================================
# Zero2 Sensor → MQTT publisher (FULL)
# TF-Luna / HLK-LD6002 / MLX90614
# - by-id固定（あなたの ls 出力に合わせ込み済み）
# - HLKが抜けても落ちない
# ============================================================

import time, json, socket, datetime, traceback
import paho.mqtt.client as mqtt
import serial
from smbus2 import SMBus

# ========= 基本 =========
ZERO2_ID = socket.gethostname()

MQTT_HOST = "192.168.8.10"
MQTT_PORT = 1883
MQTT_TOPIC = f"zero2/{ZERO2_ID}/sensor"

INTERVAL_SEC = 15 * 60
WINDOW_SEC   = 30

# ========= ポート（by-id確定） =========
TF_LUNA_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"  # ttyUSB0
TF_LUNA_BAUD = 115200

HLK_PORT = "/dev/serial/by-id/usb-Silicon_Labs_CP2104_USB_to_UART_Bridge_Controller_02BBA492-if00-port0"  # ttyUSB1
HLK_BAUD = 115200

# ========= MLX =========
MLX_I2C_ADDR = 0x5A

def read_mlx90614(bus):
    try:
        raw_amb = bus.read_word_data(MLX_I2C_ADDR, 0x06)
        raw_obj = bus.read_word_data(MLX_I2C_ADDR, 0x07)
        amb = raw_amb * 0.02 - 273.15
        obj = raw_obj * 0.02 - 273.15
        return round(amb, 2), round(obj, 2)
    except Exception:
        return None, None

def read_tfluna_once(ser):
    try:
        while True:
            b1 = ser.read(1)
            if b1 == b'\x59':
                b2 = ser.read(1)
                if b2 == b'\x59':
                    frame = ser.read(7)
                    dist = frame[0] + frame[1] * 256
                    strength = frame[2] + frame[3] * 256
                    return dist, strength
    except Exception:
        return None, None

def read_hlk_raw(ser, max_lines=40):
    lines = []
    try:
        t0 = time.time()
        while time.time() - t0 < WINDOW_SEC:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                lines.append(line)
            if len(lines) >= max_lines:
                break
    except Exception:
        pass
    return lines

def mqtt_publish(payload):
    client = mqtt.Client(client_id=f"zero2-{ZERO2_ID}", clean_session=True)
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
        client.loop_start()
        info = client.publish(MQTT_TOPIC, json.dumps(payload, ensure_ascii=False), qos=0, retain=False)
        info.wait_for_publish(timeout=3)
        client.loop_stop()
        client.disconnect()
        return True
    except Exception as e:
        print("[MQTT ERROR]", e)
        return False

def main():
    print(datetime.datetime.now(), "=== Zero2 MQTT START ===")
    print(datetime.datetime.now(), f"MQTT -> {MQTT_HOST}:{MQTT_PORT} topic={MQTT_TOPIC}")
    print(datetime.datetime.now(), f"TF_LUNA_PORT={TF_LUNA_PORT}")
    print(datetime.datetime.now(), f"HLK_PORT={HLK_PORT}")

    bus = SMBus(1)

    # TF-Luna は必須
    ser_luna = serial.Serial(TF_LUNA_PORT, TF_LUNA_BAUD, timeout=1)

    # HLK は任意（無い/抜けたらスキップ）
    ser_hlk = None
    try:
        ser_hlk = serial.Serial(HLK_PORT, HLK_BAUD, timeout=1)
        print("[HLK] connected OK")
    except Exception as e:
        print("[HLK] not available -> skip:", e)

    while True:
        started = datetime.datetime.utcnow()

        payload = {
            "meta": {
                "zero2_id": ZERO2_ID,
                "topic": MQTT_TOPIC,
                "started_utc": started.isoformat() + "Z",
                "finished_utc": None,
                "interval_sec": INTERVAL_SEC,
                "window_sec": WINDOW_SEC,
            },
            "tf_luna": {},
            "mlx90614": {},
            "hlk_ld6002": {},
        }

        try:
            d, s = read_tfluna_once(ser_luna)
            payload["tf_luna"] = {"distance_cm": d, "signal": s}

            amb, obj = read_mlx90614(bus)
            payload["mlx90614"] = {"ambient_c": amb, "object_c": obj}

            if ser_hlk:
                raw = read_hlk_raw(ser_hlk)
            else:
                raw = []

            payload["hlk_ld6002"] = {"lines": len(raw), "raw_sample": raw[:5]}

        except Exception:
            traceback.print_exc()

        payload["meta"]["finished_utc"] = datetime.datetime.utcnow().isoformat() + "Z"
        ok = mqtt_publish(payload)
        print(datetime.datetime.now(), "[SEND]", ok)

        time.sleep(INTERVAL_SEC)

if __name__ == "__main__":
    main()
