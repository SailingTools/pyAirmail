import serial
import time

ser=serial.Serial(port='\\.\COM9', baudrate=4800, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10)
ser.open()

ser.write('$PICOA,90,00,REMOTE,ON*58\r\n')

# Or channel 16562
ser.write('$CCFSI,123720,123720,m,0*01\r\n')

ser.write('$PICOA,90,08,REMOTE,OFF*1E\r\n')

ser.close()
