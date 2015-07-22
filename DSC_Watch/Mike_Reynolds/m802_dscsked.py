#!/usr/bin/python

#-----------------------------------------------------------------------------
# m802_dscsked
# A script to power up an IC-M802 for a DSC Watch sked
# Radio must have been powered down in DSC Watch.
#
# Created by Mike Reynolds of sv Zen Again (vk6hsr@gmail.com)
# Assisted by Mark Pitman of sv Tuuletar
#
# June 2015
#-----------------------------------------------------------------------------
# Notes:
#
# $CCFSI sentence format
#   tx frequency field: six characters required.
#   rx frequency field: six characters required.
#   mode field: 'm' = USB; 'o' = AM; 'q' = AFS; '{' = CW; <null> = LSB or FSK.
#   power field: always '0'.
#
# $CTFSI sentence format:
#   both frequency fields blank means either:
#     1. Radio in DSC Watch; or
#     2. Radio set to unconfigured User Channel (unlikely?).
#-----------------------------------------------------------------------------

import serial
import time


# Serial Port
ser = serial.Serial(port='/dev/tty.usbserial', \
                    baudrate=4800, \
                    bytesize=serial.EIGHTBITS, \
                    parity=serial.PARITY_NONE, \
                    stopbits=serial.STOPBITS_ONE, \
                    timeout=5)


#-----------------------------------------------------------------------------
# do_checksum function
# bytewise XOR over sentence (all characters after '$' and before '*')
def do_checksum(payload):
    ba = bytearray()
    cs = 0
    ba.extend(payload)
    for b in ba:
        cs = cs ^ b
    return format(cs, '02x')


#-----------------------------------------------------------------------------
# do_sentence function
# assemble NMEA sentence, send it, and print response
def do_sentence(payload):
    checksum = do_checksum(payload)
    command = "$" + payload + "*" + checksum.upper()

    print("#  Command:  " + command)
    ser.write(command + "\r\n")

    response = ser.readline()
    print("#  Response: " + response[:-2])


#-----------------------------------------------------------------------------
# MAIN
# Connects to radio, issues commands and disconnects
def main():

    print ()
    print("############################################################")
    print("#                       m802_dscsked                       #")
    print("############################################################")
    
    # Open connection and send a command (which is ignored) to turn radio on
    print("#\n# Open connection")
    ser.close()
    ser.open()
    do_sentence("PICOA,90,08,REMOTE,ON")

    # Get current frequency
    # Note that empty frequency fields usually indicate DSC Watch is on
    print("#\n# Read current frequency")
    do_sentence("CCFSI,,,m,0")
    time.sleep(15)

    # Close connection (turns radio off if originally off)
    print("#\n# Close connection")
    ser.close()

    print("# Done\n#")
    print("############################################################")
    print ()


#-----------------------------------------------------------------------------
# Run it!
main()


#-----------------------------------------------------------------------------
