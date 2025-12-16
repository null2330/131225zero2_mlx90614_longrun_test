# Zero2 MQTT Setup Memo

## OS
- Raspberry Pi OS (Bookworm)
- rpi-connect enabled

## Python Environment
```bash
python3 -m venv ~/z2env
source ~/z2env/bin/activate
pip install paho-mqtt smbus2
