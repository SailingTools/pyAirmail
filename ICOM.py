#!/usr/bin/python


"""
A simple script that turns on REMOTE 
and changes channel then turns 
remote off and quits
"""

import serial
import time

#ser=serial.Serial(port='\\.\COM9', baudrate=4800, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10)
ser=serial.Serial(port='/dev/ttyUSB4', baudrate=4800, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10)
#ser.open()
print("Connected to ICOM-M802")

ser.write('$PICOA,90,00,REMOTE,ON*58\r\n')
r = ser.readline()
print(r)
time.sleep(4)

ser.write('$CCFSI,123720,123720,m,0*01\r\n')
r = ser.readline()
print(r)
time.sleep(4)

ser.write('$PICOA,90,08,REMOTE,OFF*1E\r\n')
r = ser.readline()
print(r)
time.sleep(4)

print("Closing connection to ICOM-M802")
ser.close()
