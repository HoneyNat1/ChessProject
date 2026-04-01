import serial
import time
# make sure you go to device inventory to see which "port" it is
ser = serial.Serial("COM6", 115200, timeout=1)
time.sleep(2)

ser.write(b"$X\n")          # unlock GRBL
ser.write(b"G0 X300 Y200 F5000\n")  # move to X10 Y10