import serial
import time
import datetime
import threading
import math
import os

import numpy as np
import matplotlib.pyplot as plt

class modemController():

    def __init__(self, baud=57600, timeout=10):
        self.crc = None
        self.ser=serial.Serial(port='/dev/modemSCS', baudrate=baud, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=timeout, xonxoff=True)
        self.setTimeout(0.05)
        self.write()
        self.wait_full_response(printOut=True)
        return None

    def runInitCommands(self):
        commands = ['VER', 'RESTART', 'SERB', 'TRX RTS 0', 'AM', 'TR 0', 'PT', 'QRTC 4', 'ESC 27',
'PTCH 31', 'MAXE 35', 'LF 0', 'CM 0', 'REM 0', 'BOX 0', 'MAIL 0', 'CHOB 0', 'UML 0', 'TRX S 0', 'TRX DU 0',
'U *1', 'CHO 25', 'BK 24', 'FSKA 250', 'PSKA 330', 'PAC PRB 0', 'PAC CM 0', 'PAC CB 0', 'PAC M 0',
'PAC US 10', 'FR MO 0', 'SYS SERN', 'MY *SCSPTC*', 'LICENSE', 'TONES 2', 'MARK 1600', 'SPACE 1400', 
'TXD 4', 'CSD 5', 'MYcall VJN4455', 'ARX 0', 'L 0', 'CWID 0', 'CONType 3', 'MYcall VJN4455']  
        # Excluded: 'TIME 18:00:00', 'DATE 09.11.14', 'ST 2', 'TERM 4', 'MYLEV 2',
        for c in commands:
            self.write(c)
            self.wait_full_response(printOut=True)
        return None

    def setTimeout(self, timeout):
        return self.ser.setTimeout(timeout)

    def readWaiting(self):
        w = self.ser.inWaiting()
        return self.ser.read(w)

    def read(self, chunk_size=1024, retries=1, printOut=False):
        r = self.ser.read(chunk_size)
        counter = 0
        while (counter<retries):
            nr = self.ser.read(chunk_size)
            if nr:
                r += nr
            else:
                counter += 1
        if printOut:
            print(r.replace('\r','\n'))
        return r

    def wait_full_response(self, timeout=10, retries=1, rate=0.01, printOut=False):
        timeout = int(timeout)
        stop_time = time.time() + timeout
        # Wait for something to come up
        w = self.ser.inWaiting()
        if not w:
            while (not w) and (time.time() < stop_time):
                w = self.ser.inWaiting()
        # If we didn't get a response before the timeout then return None
        if not w:
            return ''
        # If we have something then see if there is more
        r = self.readWaiting()
        nr = ''
        counter=0
        while (counter<retries) and (time.time() < stop_time):
            if rate:
                time.sleep(rate)
            nr = self.readWaiting()
            if nr:
                r += nr
            else:
                counter += 1
        if printOut:
            print(r.replace('\r', '\n'))
        return r

    def write(self, cmd=''):
        self.ser.write('%s\r'%(cmd))
        return None

    def close(self):
        return self.ser.close()

    def runInit(self):
        return None

class modemHostmodeController(modemController):

    def __init__(self, baud=57600, timeout=10):
        modemController.__init__(self, baud=baud, timeout=timeout)
        self.interruptFlag = False

    def interrupt(self):
        self.interruptFlag = True
       
    def hostmode_start(self, crc=False):
        if crc:
            self.write('JHOST5')
            self.crc = crcCheck()
        else:
            self.write('JHOST1')
            self.crc = None
        return self.wait_full_response(printOut=True)

    def getChannelsWithOutput(self):
        # Poll Channel 255 to find what channels have output
        s = bytearray(self.write_and_respond('G', channel=255))
        channels = []
        for c in s[2:]:
            if (c==255) or (c==0):
                continue
            else:
                channels.append( c-1 )
        return channels

    def checkResponse(self, r, c):
        # Do some checks on the returned data
        if len(r) < 3:
            return (None, 0)
        h = bytearray(r[:3])
        d = bytearray(r[3:])
        l = h[2] + 1
        dl = len(d)
        if not h[0] == c:
            print('WARNING: Returned data does not match polled channel')
            return (None, 0)
        if not l == dl:
            print('WARNING: Data length (%i) does not match stated amount (%i)'%(dl, l))
            if dl < l:
                d.extend('\x00'*(l-dl))
            else:
                d = d[:l]
        return (d, l)
 
    def getChannelOutput(self, c, max_data_length=1024, max_retries=1, timeout=1, gpoll=True, read_length=0, report_increment=50000):
        self.interruptFlag = False
        timeout = int(timeout)
        self.response = bytearray(max_data_length)
        start_byte = 0; stop_byte = 0; ab = 0
        start_time = time.time()
        stop_time = start_time + timeout
        counter = 0 if max_retries else -1
        while (counter < max_retries) and (stop_byte < max_data_length) and (time.time() < stop_time) and (not self.interruptFlag):
            # Check to see if there is any data on this channel
            if gpoll:
                channels = self.getChannelsWithOutput()
                if not c in channels:
                    #print('No data on polled channel %i'%(c))
                    if max_retries:
                        counter += 1
                    continue
            # Get the data
            r = self.write_and_respond('G', channel=c, read_length=read_length)
            (d, l) = self.checkResponse(r, c)
            if not d:
                #print('No data on channel %i'%(c))
                if max_retries:
                    counter += 1
                continue
            # Get the place to insert in data buffer
            stop_byte = start_byte + l
            if stop_byte > max_data_length:
                stop_byte = max_data_length
            # Add the data to the buffer
            self.response[start_byte:stop_byte] = d
            # Report on progress (print out)
            if report_increment:
                bb = int(stop_byte/report_increment)
                if not ab == bb:
                    t = time.time() - start_time
                    print('Read %i kB in %f seconds [%i b/s]'%(stop_byte/1000, t, int(stop_byte/t)))
            # Increment timeouts and counters
            stop_time = time.time() + timeout
            start_byte = stop_byte
            ab = bb
        # Report the final data amount/time
        t = time.time() - start_time
        print('Read %i kB in %f seconds [%i b/s]'%(stop_byte/1000, t, int(stop_byte/t)))
        self.response = self.data[:stop_byte]
        return self.response
        
    def hostmode_quit(self):
        self.write_and_respond('JHOST0', channel=0)
        self.write()
        return self.wait_full_response(printOut=True)

    def write_bin(self, message, channel=255):
        c = self.int2hex(channel)
        l = self.int2hex(len(message)-1)
        m = message.encode('hex')
        s = '%s 01 %s %s'%(c, l, m)
        if self.crc:
            s = 'AA AA %s %s'(s, self.crc.do_calc(s.replace(' ','').decode(hex)))
        self.writeHexString(s)
        return None

    def write_and_respond(self, message, channel=255, read_length=0):
        self.write_bin(message, channel=channel)
        if read_length:
            r = self.ser.read(read_length)
            #print('Got %i bytes of data'%(len(r)))
            return r
        return self.wait_full_response(rate=0.01)

    def int2hex(self, channel):
        c = '%2s'%(hex(channel)[2:])
        return c.replace(' ', '0')

    def writeHexString(self, s):
        bs = s.replace(' ','').decode('hex')
        #print('%s [%s]'%(bs, bs.encode('hex')))
        self.ser.write(bs)
        return None

class Fax():

    def __init__(self, modem=None):
        self.modem = modemHostmodeController() if not modem else modem
        self.data = None
        self.xres = None

    def start(self):
        print('Starting hostmode fax')
        self.hostmode_start()
        self.write_and_respond('@F%s'%(start_code), channel=0)
        time.sleep(1.0)
 
    def quit(self):
        print('Closing hostmod fax')
        self.write_and_respond('@F0', channel=0)
        self.hostmode_quit()
 
    def receive_start(self, lines=200, rate=32, lines_per_minute=120):
        start_code='1' if rate==32 else '17'
        self.xres = int((float(self.ser.getBaudrate())/rate)*(float(60)/lines_per_minute))
        data_length=lines*self.fax_xres
        channels = self.modem.getChannelsWithOutput()
        if 252 in channels:
            print('Getting up to %i kB of fax data on Channel 252'%(data_length/1000))
            self.fax_thread = threading.Thread(target=self.get_fax_stream)
            self.fax_thread.daemon = True
            self.fax_thread.start()
        else:
            print('Channel 252 not streaming fax output')
            self.data = None
        return None

    def receive_stop(self):
        self.modem.interruptFlag = True

    def get_fax_stream(self):
        self.data = self.modem.getChannelOutput(252, max_data_length=data_length, max_retries=0, timeout=10, read_length=259, gpoll=False)
        return None

    def plot(self, xres=None):
        if xres is None:
            xres = self.xres
        if not self.data:
            print('No fax data aquired yet')
            return None
        a = np.array(bytearray(self.data))
        rows = len(a)/xres
        cropsize = xres*rows
        a = a[:cropsize]
        a = a.reshape((rows,xres))
        path = 'fax_images'
        os.mkdir(path) if not os.path.exists(path) else None
        fname = '%s/%s.png'%(path, datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))
        plt.imsave(fname, a, vmin=0, vmax=255, cmap='gray')
        print('Saved fax image to %s'%(fname))
        plt.imshow(a, vmin=0, vmax=255, cmap='gray')
        plt.show()
        return None

    def fax_data_compressy(self, axis=0):
        return self.data.compress([divmod(i,2)[1] for i in range(np.shape(d)[0])], axis=axis)


class crcCheck():

    def __init__(self):
        self.c = int('8408', base=16)
        self.makeCrcTable()

    def isOdd(self, num):
        return bool(divmod(num, 2)[1])

    def innerLoop(self, Data, accu=0):
        for j in range(8):
            if self.isOdd( Data^accu ):
                accu = (accu+1)^self.c
            else:
                accu = (accu+1)
            Data += 1
        return accu
 
    def makeCrcTable(self):
        self.crc_table = range(256)
        for index in range(256):
            accu = self.innerLoop(index)
            self.crc_table[index] = accu
        return self.crc_table

    def calc_crc_ccitt(self, b):
        crc = self.crc
        self.crc = ((crc + 8) & 255)^(self.crc_table[(crc^b) & 255])

    def do_calc(self, src='\x1F\x00'):
        # '\xFF\x01\x00\x47' (Standard G-poll on channel 255) Result should be 6b 55 = 27477
        # '\xFF\x01\x00' (Response to G-poll on channel 255) Result should be E7 19 = 59161
        # '\x1F\x00\x1E\x19' (Response on channel 31) Result is 1E 19 = 7705
        self.crc = int('ffff', base=16)
        ba = bytearray(src)
        for b in ba:
            self.calc_crc_ccitt(b)

        # Invert the results
        print('Before inverting: %i, %s'%(self.crc, hex(self.crc)))
        self.crc = self.crc^int('ffff', base=16)
        print('After inverting: %i, %s'%(self.crc, hex(self.crc)))

        return self.crc

