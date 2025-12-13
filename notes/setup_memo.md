# MLX90614 long-run test memo (Zero2)

## Hardware
- Raspberry Pi Zero 2 W
- MLX90614 (I2C, addr 0x5A)
- 3.3V power confirmed stable

## OS / Settings
- I2C enabled: dtparam=i2c_arm=on
- Confirmed via i2cdetect

## Python
- venv: mlxenv
- Library: smbus / smbus2

## Notes
- First ~10–15s shows unstable values
- After warm-up, ambient & object stabilize
- Safe to combine with HLK-LD6002 & TF-LUNA
