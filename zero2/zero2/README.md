# Zero2 MQTT Sensor Publisher

This directory contains the MQTT publishing components
running on Raspberry Pi Zero 2 W.

## Overview

- Device: Raspberry Pi Zero 2 W
- Role: Sensor node (publisher only)
- Communication: MQTT → Raspberry Pi 5 (broker / subscriber)

## Files

- `zero2_sensors_mqtt.py`  
  Reads sensors (MLX90614 / TF-Luna / HLK-LD6002)  
  Publishes data via MQTT

- `zero2-mqtt.service`  
  systemd oneshot service to run the MQTT publisher

- `zero2-mqtt.timer`  
  systemd timer (runs every 15 minutes)

## Execution Flow

1. systemd timer triggers
2. systemd service runs
3. Python script publishes MQTT payload
4. Script exits (no daemon)

## Notes

- This node does **not** store data locally
- All processing and storage is handled by Pi5
