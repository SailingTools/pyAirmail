import Tkinter as tk
from Tkconstants import *
import ttk

import time
from widgets import LabeledEntry
from icom import radio

import threading

class AppScanner(ttk.Frame):

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.pack(fill=X)

        self.startFreq = LabeledEntry(self, labelText = "Start Frequency [kHz]:", entryWidth = 8, entryValidateStr = r'^[0-9]*\.?[0-9]?$')
        self.startFreq.pack(fill=X, side=TOP)
        self.startFreq.set('12000.0')

        self.stopFreq = LabeledEntry(self, labelText = "Stop Frequency [kHz]:", entryWidth = 8, entryValidateStr = r'^[0-9]*\.?[0-9]?$')
        self.stopFreq.pack(fill=X)
        self.stopFreq.set('12100.0')

        self.incFreq = LabeledEntry(self, labelText = "Increments [kHz]:", entryWidth = 8, entryValidateStr = r'^[0-9]*\.?[0-9]?$')
        self.incFreq.pack(fill=X)
        self.incFreq.set('10.0')

        self.waitTime = LabeledEntry(self, labelText = "Seconds per Frequency [s]:", entryWidth = 8, entryValidateStr = r'^[0-9]*\.?[0-9]?$')
        self.waitTime.pack(fill=X)
        self.waitTime.set('1.0')

        buttons = ttk.Frame(self)
        buttons.pack(fill=X)

        self.button_start = tk.Button(buttons, text="Start Scan", command=self.start_scan)
        self.button_start.pack(side=LEFT)
        self.button_stop = tk.Button(buttons, text="Stop",command=self.stop_scan)
        self.button_stop.pack(side=RIGHT)

        self.scanThread = threading.Thread(target=self.do_scan)
        self.scanThread.daemon = True
        self.stopper = False
        return None

    def start_scan(self):
        self.scanThread.start()

    def do_scan(self):
        self.stopper = False
        f_start = int(float(self.startFreq.get())*10)
        f_stop = int(float(self.stopFreq.get())*10)
        f_inc = int(float(self.incFreq.get())*10)
        w_time = float(self.waitTime.get())
        print "Starting Scanning from %.01f kHz to %.01f kHz with %.01f"%(float(f_start/10.0), float(f_stop/10.0), float(f_inc/10.0))
        
        # Get all the frequencies to scan
        freqs = range(f_start, f_stop, f_inc)
        if not freqs[-1] == f_stop:
            freqs += [f_stop]
        print "Scanning will take %.01f"%(w_time*len(freqs))

        # Scan through all the frequencies
        radio.start_radio()
        radio.remote(True)
        for freq in freqs:
            if self.stopper:
                break
            resp = radio.setFrequency(freq)
            time.sleep(w_time)

        # Turn off remote 
        radio.remote(False)
        radio.close()
        return None

    def stop_scan(self):
        self.stopper = True