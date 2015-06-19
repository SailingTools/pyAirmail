#!/usr/bin/python


"""
A simple script that:
1 - Connects to the ICOM-M802 via serial port on COM9 (Windows) or ttyUSB4 (Linux).  Adjust the COM/TTY ports to match your system setup. Comment out lines 14/15 depending on if you are Linux/Windows based.  This is the call that will turn on the ICOM-M802 head-unit if it is off.

2 - "$PICOA,90,00,REMOTE,ON*58" - turns on REMOTE mode

3 - "$CCFSI,123720,123720,m,0*01" - changes channel (to 12,372.0 kHz)

4 - "ser.close()" closed the serial connection.  This will turn off the ICOM head-unit again at that point.

NOTE:  If you manually turn on your radio and set it to DSC watch-mode then turn it off.  Then when the below script is run it will turn on in watch mode.  If you skip (comment-out) the middle three steps then it will turn-off the radio while still in DSC watch mode.  This is a good method for turning the radio on in DSC-watch mode periodically to listen for DSC calls or position reports.  

If all cruisers run the same script that turns the radio on DSC watch at particular times throughout the day then you could keep an almost-continuous watch with very low power.  If the clocks across all the boats were well-synced then you could have the radio turn on for scan just 2-3 minutes every hour.  This would reduce watch-time to 60-minutes or so per day and consume only 2 or 3 amp-hours.

If you run the middle 3 lines then the radio will be bumped out of DSC watch-mode.

----------------
Some info/resources for more information:
http://www.catb.org/gpsd/NMEA.txt
http://mvvikingstar.blogspot.com.au/2012/10/connecting-and-debugging-your-icom-m802.html

The following page provides evidence that you can control DSC communication via the NMEA interface:
http://continuouswave.com/whaler/reference/DSC_Datagrams.html

The following pages provide info on proprietary NEAM sentences:
http://fort21.ru/download/NMEAdescription.pdf
https://www8.garmin.com/support/pdf/NMEA_0183.pdf
http://www.icomuk.co.uk/files/icom/PDF/productManual/MXP-5000_MXD-5000_Installation_0.pdf
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
