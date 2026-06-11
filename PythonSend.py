import serial
import time

ser = serial.Serial('COM3',115200, timeout=2)

time.sleep(0.1)  # let port settle

# Read the "Ready" message
print(ser.readline().decode().strip())

def send_cmd(c):
    ser.write(c.encode())

    time.sleep(0.1)

    while ser.in_waiting:
        print("[RX]", ser.readline().decode(errors="ignore"))


ser.close()