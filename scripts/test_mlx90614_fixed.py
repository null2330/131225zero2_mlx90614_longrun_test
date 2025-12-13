from smbus2 import SMBus, i2c_msg
import time

I2C_BUS = 1
ADDR = 0x5A

REG_AMBIENT = 0x06
REG_OBJECT  = 0x07

def read_temp(bus, reg):
    # レジスタ指定
    write = i2c_msg.write(ADDR, [reg])
    # データ2バイト読み出し（PECなし）
    read = i2c_msg.read(ADDR, 2)

    bus.i2c_rdwr(write, read)

    data = list(read)
    raw = data[0] | (data[1] << 8)   # little-endian

    # 温度変換（データシート通り）
    temp_c = raw * 0.02 - 273.15
    return temp_c

def main():
    with SMBus(I2C_BUS) as bus:
        for i in range(10):
            try:
                ta = read_temp(bus, REG_AMBIENT)
                to = read_temp(bus, REG_OBJECT)
                print(f"[{i+1:02d}] Ambient = {ta:.2f} °C   Object = {to:.2f} °C")
                time.sleep(1)
            except Exception as e:
                print("Error:", e)
                break

if __name__ == "__main__":
    main()
