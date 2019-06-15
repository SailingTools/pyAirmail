#!/usr/bin/python

"""
m802_DSCsched.py

A script to power up and configure an IC-M802 for a DSC sked.  ENSURE YOUR RADIO IS IN DSC WATCH MODE AND THEN TURNED OFF BEFORE YOU RUN THIS SCRIPT.

Created by Mark Pitman of sv Tuuletar and Mike Reynolds of sv Zen Again (vk6hsr@gmail.com)

This script requires the following python libraries to be installed:
 * apscheduler (pip install apscheduler)
 * python-serial (sudo apt-get install python-serial)
"""

from apscheduler.schedulers.blocking import BlockingScheduler
import serial
import time
import os

ser=serial.Serial(port='/dev/icom802', baudrate=4800, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10)

START_HOURS = '0-23'
STOP_HOURS = '0-23'
START_MINS = '0,30'
STOP_MINS = '1,31'

def do_checksum(payload):
    ba = bytearray()
    cs = 0
    ba.extend(payload)
    for b in ba:
        cs = cs ^ b
    return format(cs, '02x')

def do_sentence(payload):
    checksum = do_checksum(payload)
    command = "$" + payload + "*" + checksum.upper()
    print("#  Command:  " + command)
    ser.write(command + "\r\n")
    response = ser.readline()
    print("#  Response: " + response[:-2])
    return response

def start_radio():
    print "Starting ICOM-M802"
    ser.close(); ser.open()
    do_sentence("STARTUP") 

def stop_radio():
    print("Closing connection to ICOM-M802")
    ser.close()

if __name__ == "__main__":
    sched = BlockingScheduler()

    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    # Schedules job_function to be run for 1 minute on the hour and half-hour
    sched.add_job(start_radio, 'cron', hour=START_HOURS, minute=START_MINS, timezone='utc')
    sched.add_job(stop_radio, 'cron', hour=STOP_HOURS, minute=STOP_MINS, timezone='utc')
    
    print('The following schedule is currently defined:')
    print(' - Radio turning ON  at HOURS: %s MINS: %s'%(START_HOURS, START_MINS))
    print(' - Radio turning OFF at HOURS: %s MINS: %s'%(STOP_HOURS, STOP_MINS))

    try:
        print('Starting schedule NOW')
        sched.start()
    except (KeyboardInterrupt, SystemExit):
        pass