from smbus2 import SMBus, i2c_msg
import time

I2C_BUS = 1
ADDR = 0x5A

REG_AMBIENT = 0x06
REG_OBJECT  = 0x07

WARMUP_SEC = 60     # ウォームアップ時間（秒）
INTERVAL   = 1.0    # 測定間隔（秒）

def read_temp(bus, reg):
    write = i2c_msg.write(ADDR, [reg])
    read  = i2c_msg.read(ADDR, 2)
    bus.i2c_rdwr(write, read)

    data = list(read)
    raw = data[0] | (data[1] << 8)
    temp_c = raw * 0.02 - 273.15
    return temp_c

def main():
    with SMBus(I2C_BUS) as bus:
        print("=== MLX90614 long-run evaluation ===")
        print(f"Warm-up: {WARMUP_SEC} sec")
        print("Warming up...", end="", flush=True)

        for _ in range(WARMUP_SEC):
            try:
                read_temp(bus, REG_AMBIENT)
                time.sleep(1)
                print(".", end="", flush=True)
            except Exception:
                pass

        print("\n--- Measurement start (Ctrl+C to stop) ---")

        start = time.time()
        count = 1

        while True:
            ta = read_temp(bus, REG_AMBIENT)
            to = read_temp(bus, REG_OBJECT)
            elapsed = time.time() - start

            print(
                f"[{count:05d}] "
                f"t={elapsed:7.1f}s  "
                f"Ambient={ta:6.2f} °C  "
                f"Object={to:6.2f} °C"
            )

            count += 1
            time.sleep(INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
