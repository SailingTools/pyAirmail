import Tkinter as tk
from Tkconstants import *
import ttk

import json

from icom import radio
from widgets import LabeledEntry

from modem import modem_socket
import sailmail
import threading

class AppEmail(ttk.Frame):

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master)
        self.pack(fill=BOTH, expand=1)

        self.currentStation = 0
        self.currentFrequency = 0
        self.radioFrequency = 0
        self.connectType = 0
        self.disconnecting = False
        self.readStationInfo()
        
        self.modem_socket = None
        self.email_thread = None

        self.drawMenu()

    def updateMenus(self):
        self.stationDropDown.current(self.currentStation)
        self.freqDropDown['values'] = ['%.01f'%(f) for f in self.get_frequencies()]
        self.freqDropDown.current(self.currentFrequency)
        
    def drawMenu(self):
        stationFrame = tk.Frame(self, relief=RIDGE, borderwidth=2)
        stationFrame.pack(fill=X, expand=1)

        self.connectDropDown = ttk.Combobox(stationFrame, validatecommand = self.setConnectType, validate='all', values=['Telnet', 'HF Radio'])
        self.connectDropDown.pack(fill=X, expand=1)
        self.connectDropDown.state(['readonly'])
        self.connectDropDown.current(self.connectType)

        self.stationDropDown = ttk.Combobox(stationFrame, validatecommand = self.listLink, validate = 'all', values = self.get_stations())
        self.stationDropDown.current(self.currentStation)
        self.stationDropDown.state(['disabled', 'readonly'])
        self.stationDropDown.pack(side=LEFT)

        self.freqDropDown = ttk.Combobox(stationFrame, validatecommand = self.setFrequency, validate = 'all', values = ['%.01f'%(f) for f in self.get_frequencies()] )
        self.freqDropDown.current(self.currentFrequency)
        self.freqDropDown.state(['disabled', 'readonly'])
        self.freqDropDown.pack(side=RIGHT)

        self.textbox = tk.Text(self)
        self.textbox.pack(fill=X, expand=1)

        self.button_connect = tk.Button(self, text="Connect", command=self.connect)
        self.button_connect.pack(side=LEFT)
        self.button_disconnect = tk.Button(self, text="Disconnect",command=self.disconnect)
        self.button_disconnect.pack(side=RIGHT)

    def setConnectType(self):
        if not self.connectDropDown.current() == self.connectType:
            self.connectType = self.connectDropDown.current()
            if self.connectType == 1:
                self.stationDropDown.state(['!disabled'])
                self.freqDropDown.state(['!disabled'])
                radio.start_radio()
                radio.remote(True)
                self.setFrequency()
                self.modem_socket = modem_socket("VJN4455")
            else:
                self.stationDropDown.state(['disabled'])
                self.freqDropDown.state(['disabled'])
                radio.remote(False)
                radio.close()
                self.modem_socket.close()
                self.modem_socket = None
        return True

    def setFrequency(self):
        self.currentFrequency = self.freqDropDown.current()
        freq = int(self.get_current_frequency()*10) - 15
        if not self.radioFrequency == freq:
            self.radioFrequency = freq
            resp = radio.setFrequency(freq)
        return True

    def showText(self, text, index='500000.0'):
        self.textbox.insert(index,text+'\n')
        self.textbox.see(index)

    def disconnect(self):
        if self.disconnecting:
            print('Forcing Disconnect...')
            self.modem_socket.force_disconnect()
        else:
            print('Disconnecting...')
            self.modem_socket.disconnect()
            self.disconnecting = True
        return None

    def _connect(self):
        if self.connectType == 1:
            station = self.stations.keys()[self.currentStation]
            sailmail.send_and_receive(mode='Pactor', station=station, socket=self.modem_socket)
        else:
            sailmail.send_and_receive(mode='Telnet')
        return None

    def connect(self):
        self.email_thread = threading.Thread(target=self._connect)
        self.email_thread.daemon = True
        self.email_thread.start()
        return None

    def readStationInfo(self):
        f = open('stations.txt','r')
        d = json.load(f)
        f.close()
        self.stations = d['sailmail']['stations']
        self.frequencies = d['sailmail']['frequencies']
        return None

    def listLink(self):
        if not self.stationDropDown.current() == self.currentStation:
            self.currentStation = self.stationDropDown.current()
            self.freqDropDown['values'] = ['%.01f'%(f) for f in self.get_frequencies()]
            self.freqDropDown.current(0)
            self.setFrequency()
        return True

    def get_stations(self):
        return ['%s: %s'%(i[0], i[1].split(';')[-1]) for i in self.stations.items()]

    def get_frequencies(self):
        station = self.stations.keys()[self.currentStation]
        return self.frequencies[station]

    def get_current_frequency(self):
        return self.get_frequencies()[self.freqDropDown.current()]
