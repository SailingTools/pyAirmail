#!/usr/bin/python


"""
A simple script that connects to the PTC-IIex modem
and sends some simple commands then shuts down.
"""

import serial
import time

# It is either /dev/ttyUSB1 or /dev/ttyUSB3
ser=serial.Serial(port='/dev/ttyUSB1', baudrate=4800, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10)
#ser.open()
print("Connected to PTC-IIex")


print("Closing connection to PTC-IIex")
ser.close()
