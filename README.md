# Zero2 MLX90614 Long-Run Test

This repository documents a stable long-run evaluation of the MLX90614 infrared temperature sensor on Raspberry Pi Zero 2 W.

## Purpose
- Verify stable continuous output
- Measure warm-up behavior
- Prepare for multi-sensor integration:
  - HLK-LD6002 (60GHz radar)
  - TF-LUNA (LiDAR)

## Status
✅ Stable after warm-up  
✅ No I2C errors  
✅ Ready for MQTT integration

## Directory
- scripts/: test scripts
- logs/: sample outputs
- notes/: setup & troubleshooting memo
