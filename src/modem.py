import serial
import time
import datetime
import threading
import math
import os
import pytz

import numpy as np
import matplotlib.pyplot as plt

class modemController():

    def __init__(self, baud=57600, timeout=0.05):
        self.crc = None
        self.cmdinf = '01'
        self.ser=serial.Serial(
            port='/dev/pactor', 
            baudrate=baud, 
            bytesize=serial.EIGHTBITS, 
            parity=serial.PARITY_NONE, 
            stopbits=serial.STOPBITS_ONE, 
            timeout=timeout, 
            xonxoff=False
        )
        self.hostmode_quit()
        self.write_and_get_response('')
        self.restart()
        self.response = None
        self.interruptFlag = False
        self.hostmode = False
        self.good_chunks = 0

        self.init_commands = ['VER', 'RESTART', 'SERB', 'TRX RTS 0', 'AM', 'TR 0', 'PT', 'QRTC 4', 'ESC 27',
'PTCH 31', 'MAXE 35', 'LF 0', 'CM 0', 'REM 0', 'BOX 0', 'MAIL 0', 'CHOB 0', 'UML 0', 'TRX S 0', 'TRX DU 0',
'U *1', 'CHO 25', 'BK 24', 'FSKA 250', 'PSKA 330', 'PAC PRB 0', 'PAC CM 0', 'PAC CB 0', 'PAC M 0',
'PAC US 10', 'FR MO 0', 'SYS SERN', 'MY *SCSPTC*', 'LICENSE', 'TONES 2', 'MARK 1600', 'SPACE 1400', 
'TXD 4', 'CSD 5', 'MYcall VJN4455', 'ARX 0', 'L 0', 'CWID 0', 'CONType 3', 'MYcall VJN4455']  
        # Excluded: 'TIME 18:00:00', 'DATE 09.11.14', 'ST 2', 'TERM 4', 'MYLEV 2',

    def runInitCommands(self):
        for c in self.init_commands:
            if c == 'RESTART':
                self.restart()
            else:
                self.write_and_get_response(c, printOut=True)
            time.sleep(0.2)
        return None

    def setTimeout(self, timeout):
        self.ser.timeout = timeout
        return self.ser.timeout

    def read(self, chunk_size=1024, retries=0, printOut=False):
        r = self.ser.read(chunk_size)
        counter = 0
        while (counter < retries):
            nr = self.ser.read(chunk_size)
            if nr:
                r += nr
            else:
                counter += 1
        if self.crc:
            r = self.crc.decode(r)
        if printOut:
            print(r.replace('\r','\n'))
        return r

    def write(self, cmd='', newline='\r', channel=None):
        if channel is None:
            self.ser.write('%s%s'%(cmd, newline))
        else:
            self.write_channel(cmd, channel=channel)
        return None

    def write_and_get_response(self, command, newline='\r', channel=None, chunk_size=1024, retries=0, printOut=False):
        self.write(command, newline=newline, channel=channel)
        return self.read(chunk_size=chunk_size, retries=retries, printOut=printOut)

    def encode(self, message, channel):
        c = self.int2hex(channel)
        l = self.int2hex(len(message)-1)
        m = message.encode('hex')
        s = '%s %s %s %s'%(c, self.cmdinf, l, m)
        if self.crc:
            s = self.crc.encode(s)
        return s

    def write_channel(self, message, channel=255):
        self.writeHexString(self.encode(message, channel))
        self.incrementCounter()
        return None

    def incrementCounter(self, ):
        if self.crc:
            self.cmdinf = '81' if self.cmdinf == '01' else '01'
        return None

    def restart(self):
        t = self.ser.timeout
        self.setTimeout(1.0)
        self.write_and_get_response('RESTART', printOut=True)
        self.setTimeout(t)
        return None

    def close(self):
        return self.ser.close()

    def interrupt(self):
        self.interruptFlag = True
       
    def hostmode_start(self, crc=False):
        if crc:
            self.write('JHOST5')
            self.crc = crcCheck()
        else:
            self.write('JHOST1')
            self.crc = None
        self.hostmode = True
        return self.read(printOut=True)

    def hostmode_quit(self):
        self.write_and_get_response('JHOST0', channel=0)
        self.hostmode = False
        return self.write_and_get_response('',printOut=True)

    def getChannelsWithOutput(self):
        # Poll Channel 255 to find what channels have output
        s = bytearray(self.write_and_get_response('G', channel=255))
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
            print('WARNING: Data length (%i) does not match stated amount (%i). After %i good chunks.'%(dl, l, self.good_chunks))
            self.good_chunks = 0
            if dl < l:
                d.extend('\x00'*(l-dl))
            else:
                d = d[:l]
        else:
            self.good_chunks += 1
        #   print('Good chunk')
        return (d, l)
 
    def getChannelOutput(self, c, max_data_length=1024, max_retries=1, timeout=1, gpoll=False, chunk_size=1024, report_increment=50000):
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
            r = self.write_and_get_response('G', channel=c, chunk_size=chunk_size)
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
        self.response = self.response[:stop_byte]
        return self.response
        
    def int2hex(self, channel):
        c = '%2s'%(hex(channel)[2:])
        return c.replace(' ', '0')

    def writeHexString(self, s):
        bs = s.replace(' ','').decode('hex')
        #print('%s [%s]'%(bs, bs.encode('hex')))
        self.ser.write(bs)
        return None

#modem = modemController()

######################
# Modem Socket class for compatability with Sailmail Telnet sockets 
######################

class modem_socket():

    def __init__(self, mycall):
        self._mycall = mycall
        self.recv_buffer = bytearray()

        print('Initialising modem')
        self.modem = modemController()

        print('Running init commands')
        commands = ['MYcall %s'%(self._mycall), 'PTCH 31', 'MAXE 35',
            'LF 0', 'CM 0', 'REM 0', 'BOX 0', 'MAIL 0', 'CHOB 0', 'UML 0',
            'TONES 4', 'MARK 1600', 'SPACE 1400', 'CWID 0', 'CONType 3']
        for c in commands:
            self.modem.write_and_get_response(c, printOut=True)

        self.modem.hostmode_start()
        return None

    def readto(ser, end="cmd:", line=''):
        if not ser.inWaiting():
            return None
        while not line[-5:] == end:
            line += ser.read(1)
        lines = line.split('\r')
        return lines

    def breakin(self):
        return self.send('%I')

    def hostmode_init(self):
        commands = ['#TONES 4', '#MYLEV 3', '#CWID 0', '#CONType 3', 'I %s'%(self._mycall)]
        for c in commands:
            self.modem.write_and_get_response(c, channel=31)

    def connect(self, targetcall):
        self.modem.write_channel('C %s'%(targetcall), channel=31)
        
    def disconnect(self):
        self.modem.write_channel('D', channel=31)
        return None

    def force_disconnect(self):
        self.modem.write_channel('DD', channel=31)

    def send(self, msg):
        return self.modem.write_channel(msg, channel=31)

    def recv(self, size):
        c = 31
        chunk_size=10240
        output = bytearray()
        # Check and get whatever is in the receive buffer
        channels = self.modem.getChannelsWithOutput()
        if c in channels:
            r = self.modem.write_and_get_response('G', channel=c, chunk_size=chunk_size)
            (d, l) = self.modem.checkResponse(r, c)
            if d:
                self.recv_buffer += d
                print(str(d))
        # Get the number of bytes requested from the recv_buffer
        for i in range(size):
            if self.recv_buffer:
                output += bytearray([self.recv_buffer.pop(0)])
            else:
                break
        # Return bytes as a string
        return str(output)

    def close(self):
        self.modem.hostmode_quit()
        self.modem.close()
        return None

#####################
# Fax Controller
#####################

class Fax():

    def __init__(self, baud=57600, timeout=0.05, modem=None):
        self.modem = modemController(baud=baud, timeout=timeout) if not modem else modem
        self.baud = self.getBaudrate()
        self.ptch = 31
        self.data = None
        self.xres = None
        self.data_rate = None
        self.max_data_length=(1024*4000)
        self.timeout = 10
        self.chunk = ''
        self.chunk_lock = threading.Lock()
        self.apt_lock = threading.Lock()
        self.record_lock = threading.Lock()

        self.record_flag = False
        self.apt_flag = False
        self.receive_flag = False
        self.gui_callback = None

        self.runInitCommands()

    def runInitCommands(self):
        self.modem.init_commands = ['VER', 'RESTART', 'SERB', 'TRX RTS 1', 'AM', 'TR 0', 'PT', 'QRTC 4', 'ESC 27', 'PTCH %i'%(self.ptch), 'MAXE 35', 'LF 0', 'CM 0', 'REM 0', 'BOX 0', 'MAIL 0', 'CHOB 0', 'UML 0', 'TRX S 0', 'TRX DU 0', 'U *1', 'CHO 25', 'BK 24', 'ST 2', 'PAC PRB 0', 'PAC CM 0', 'PAC CB 0', 'PAC M 0', 'PAC US 10', 'FR MO 0', 'SYS SERN', 'MY *SCSPTC*', 'LICENSE']
        #Excluded: 'TERM 4', 'TIME 17:35:46', 'DATE 04.04.16'
        return self.modem.runInitCommands()

    def start(self, rate=16, lines_per_minute=120, hostmode=True):
        if hostmode:
            self.modem.hostmode_start()
            time.sleep(0.5)
        # Now start up the fax stream
        if self.modem.hostmode:
            self.data_rate = self.getBaudrate()/rate
            self.xres = int(self.data_rate*(float(60)/lines_per_minute))
            print('Starting modem hostmode fax streaming at baudrate/%i = %i bytes/s'%(rate, self.data_rate))
            start_code='1' if rate==32 else '17'
            for p in ['%M1', '#FAX Dev 500', '#FAX FR 3', '#FAX MB %s'%(int(self.baud))]:
                print('Writing hostmode command: %s'%(p))
                self.modem.write_and_get_response(p, channel=self.ptch)
                time.sleep(0.5)
            self.modem.write_and_get_response('@F%s'%(start_code), channel=self.ptch)
        else:
            self.data_rate = int(38400.0/10.0)
            self.xres = int(self.data_rate*(float(60)/lines_per_minute))
            self.modem.write('FAX Mbaud 38400')
            self.modem.write('FAX Fmfax')
        # Start reading in data chunks and 
        # monitoring for apt start/stop signals
        time.sleep(0.5)
        #self.receive_start()
        #self.apt_start()
 
    def quit(self):
        if self.modem.hostmode:
            print('Closing hostmode fax')
            self.apt_stop()
            time.sleep(0.6)
            self.receive_stop()
            time.sleep(0.1)
            self.modem.write_and_get_response('@F0', channel=self.ptch)
            self.modem.hostmode_quit()
        else:
            print('Sending term signal 255 to modem')
            self.modem.write('\xff', newline='')
            time.sleep(0.5)
            self.modem.ser.readall()

    def close(self):
        self.modem.close()

    def getBaudrate(self):
        return self.modem.ser.baudrate

    def clear_buffer(self):
        if self.modem.hostmode:
            print('Clearing Fax Data Buffer')
            self.modem.write_and_get_response('@F', channel=self.ptch, printOut=True)
        return None

    def record_start(self):
        print('Starting Recording of Fax Stream')
        self.record_thread = threading.Thread(target=self.do_record)
        self.record_thread.daemon = True
        self.record_thread.start()
        
    def do_record(self, report_increment=50000):
        print('Recording up to %i kB of fax data from channel 252'%(self.max_data_length/1000))
        self.record_flag = True
        if self.gui_callback:
            self.gui_callback()
        stop_time = time.time() + self.timeout
        self.data = bytearray(self.max_data_length)
        start_byte = 0; stop_byte = 0; ab = 0
        start_time = time.time()
        self.record_lock.acquire()
        while (stop_byte < self.max_data_length) and (time.time() < stop_time) and self.record_flag:
            # Get the latest data chunk 
            self.record_lock.acquire()
            d = self.chunk
            # Get the place to insert in data buffer
            stop_byte = self.max_data_length if stop_byte > self.max_data_length else start_byte + 256
            # Add the data to the buffer
            self.data[start_byte:stop_byte] = d
            # Report on progress (print out)
            if report_increment:
                bb = int(stop_byte/report_increment)
                if not ab == bb:
                    t = time.time() - start_time
                    print('Read %i kB in %f seconds [%i b/s]'%(stop_byte/1000, t, int(stop_byte/t)))
            # Increment timeouts and counters
            stop_time = time.time() + self.timeout
            start_byte = stop_byte
            ab = bb
        if self.record_lock.locked():
            self.record_lock.release()
        self.record_flag = False
        t = time.time() - start_time
        print('Read %i kB in %f seconds [%i b/s]'%(stop_byte/1000, t, int(stop_byte/t)))
        self.data = self.data[:stop_byte]
        self.plot(align_data=True)
        print('Stopped recording fax')
        if self.gui_callback:
            self.gui_callback()
 
    def record_stop(self):
        self.record_flag = False

    def receive_start(self):
        if self.modem.hostmode:
            channels = self.modem.getChannelsWithOutput()
            if not 252 in channels:
                print('Channel 252 not streaming fax output')
                return None
        print('Starting receiving fax data on channel 252')
        self.monitor_thread = threading.Thread(target=self.get_chunk)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        return None

    def receive_stop(self):
        self.receive_flag = False

    def get_chunk(self, max_retries=10, report_increment=0):
        #print("Timeout = %f"%(self.modem.ser.timeout))
        #self.clear_buffer()

        self.receive_flag = True
        start_time = time.time()
        stop_time = start_time + self.timeout
        retries = 0
        chunk_counter = 0
        ab = 0
        while (time.time() < stop_time) and (retries < max_retries) and self.receive_flag:
            # Get a chunk (depending on if we are in hostmode or not)
            if self.modem.hostmode:
                c = 252
                r = self.modem.write_and_get_response('G', channel=c, chunk_size=259)
                (d, l) = self.modem.checkResponse(r, c)
            else:
                l = 256
                d = self.modem.read(chunk_size=l)
            # If we have a valid chunk then process it otherwise increment the retry counter
            if (l == 256):
                retries = 0
                stop_time = time.time() + self.timeout
                self.chunk = d
                chunk_counter += 1
                # Tell the record and apt loops that it can proceed with new chunk
                if self.record_lock.locked():
                    self.record_lock.release()
                if self.apt_lock.locked():
                    self.apt_lock.release()
            else:
                if retries > 0:
                    print('Retrying (Length = %i, Chunks = %i)'%(l, chunk_counter))
                #self.clear_buffer()
                retries += 1
            # Do some reporting if asked for it
            if report_increment:
                stop_byte = chunk_counter*256
                bb = int(stop_byte/report_increment)
                if not ab == bb:
                    t = time.time() - start_time
                    print('Received %i kB in %f seconds [%i b/s]'%(stop_byte/1000, t, int(stop_byte/t)))
                ab = bb
        self.receive_flag = False
        print('Stopped receiving fax data')
        return None

    def apt_start(self):
        print('Starting APT monitoring')
        self.apt_flag = True
        self.apt_thread = threading.Thread(target=self.apt_monitor)
        self.apt_thread.daemon = True
        self.apt_thread.start()

    def apt_stop(self):
        self.apt_flag = False

    def apt_monitor(self, frequency=0.25, retries=10):
        # Analyse data packets every <frequency> seconds,
        # Once a signal is found then try to get <retries> continuous signals before 
        stop_time = time.time() + self.timeout
        counter = 0
        self.apt_lock.acquire()
        while (time.time() < stop_time) and self.apt_flag:
            self.apt_lock.acquire()
            d = self.chunk; 
            if not self.record_flag:
                if self.is_apt_signal(d, frequency=12):
                    print('Found APT Start Signal #%i'%(counter))
                    counter += 1
                    if counter > retries:
                        print('Starting Fax Recording')
                        self.record_start()
                    continue
            else:
                if self.is_apt_signal(d, frequency=8):
                    print('Found APT Stop Signal #%i'%(counter))
                    counter += 1
                    if counter > retries:
                        print('Stopping Fax Recording')
                        self.record_stop()
                    continue
            time.sleep(frequency)
            counter = 0
            stop_time = time.time() + self.timeout
        if self.apt_lock.locked():
            self.apt_lock.release()
        self.apt_flag = False
        print('Stopping APT Monitor')
        return None

    def get_fax_stream(self):
        print('Getting up to %i kB of fax data on Channel 252'%(self.max_data_length/1000))
        self.data = self.modem.getChannelOutput(252, max_data_length=self.max_data_length, max_retries=0, timeout=10, chunk_size=259, gpoll=False)
        self.plot()
        return None

    def plot(self, fname=None, xres=None, show_image=False, save_image=True, save_data=True, align_data=False):
        if xres is None:
            xres = self.xres
        if not self.data:
            print('No fax data aquired yet')
            return None
        if align_data:
            self.align_data()
        a = np.array(bytearray(self.data))
        rows = len(a)/xres
        cropsize = xres*rows
        a = a[:cropsize]
        a = a.reshape((rows,xres))
        path = 'fax_images'
        os.mkdir(path) if not os.path.exists(path) else None
        timezone = pytz.timezone('utc')
        utctime = datetime.datetime.now(tz=timezone)
        if not fname:
            fname = '%s/%s.png'%(path, utctime.strftime('%Y-%m-%d_%H%M%S'))
        if save_image:
            plt.imsave(fname, a, vmin=0, vmax=255, cmap='gray')
            print('Saved fax image to %s'%(fname))
        if save_data:
            bin_fname = fname.replace('.png', '.bin')
            self.save_data(bin_fname)
            print('Saved binary fax data to %s'%(bin_fname))
        if show_image:
            plt.imshow(a, vmin=0, vmax=255, cmap='gray')
            plt.show()
        return None

    def fax_data_compressy(self, axis=0):
        return self.data.compress([divmod(i,2)[1] for i in range(np.shape(d)[0])], axis=axis)

    def save_data(self, fname):
        f = open(fname, 'wb')
        f.write(self.data)
        f.close()
        return None

    def load_data(self, fname):
        f = open(fname, 'rb')
        self.data  = f.read()
        f.close()
        self.xres = 1800

    def is_apt_signal(self, data, frequency=12, width=1):
        # frequency=12 (start), frequency=8 (stop)
        signal_pixel_width = frequency*self.xres/1800
        l = len(data)/2
        # Crop the spectrum info and take only the real part
        s = np.abs(np.fft.fft(np.array(bytearray(data))))
        s = s.real[1:l]
        band_centre = (2*l/signal_pixel_width)
        spectrum_average = np.average(np.abs(s))
        band_average = np.average(np.abs(s[band_centre-width:band_centre+width]))
        if band_average > spectrum_average*5:
            return True
        return False

    def align_data(self, lines=[20,30,40]):
        n = len(lines)
        offset = 0.0
        counter = 0
        for line in lines:
            t = self.get_image_offset(line)
            if counter:
                if abs(t-offset) > 30:
                    print("Alignment data could not be ascertained")
                    return None
            # Keep a running average of the offset
            counter += 1
            offset = (offset*(counter-1) + t)/counter
        offset = int(offset)
        print('Aligning data with offset of %i'%(offset))
        self.data = self.data[offset:]
        return None

    def get_image_offset(self, line, signal_width=90):
        h = signal_width / 2
        d = self.data[line*self.xres:(line+1)*self.xres] 
        l = np.array(bytearray(d[-1*h:] + d + d[:h]))
        a = np.zeros(self.xres)
        for i in range(h, self.xres + h):
            a[i-h] = np.average(l[i-h:i+h])
        return a.argmax()

class crcCheck():

    def __init__(self):
        self.c = int('8408', base=16)
        self.makeCrcTable()

    def encode(self, s):
        return 'AA AA %s %s'%(self.stuff(s), self.do_calc(s))

    def decode(self, s, check_crc=True):
        if not len(s) > 4:
            print('WARNING: Response not long enough for CRC check')
            return s
        crc = s[-2:]
        body = self.destuff(s[2:-2])
        if check_crc:
            if not self.do_calc(body.encode('hex')).decode('hex') == crc:
                print('WARNING: CRC check failed')
        return body

    def destuff(self, s):
        return ''.join([s[i] for i in range(len(s)) if (i==0) or (s[i-1] != '\xaa')])

    def stuff(self, s):
        return s.upper().replace('AA', 'AA 00') 

    def isOdd(self, num):
        return bool(divmod(num, 2)[1])

    def innerLoop(self, Data, accu=0):
        for j in range(8):
            if self.isOdd( Data^accu ):
                accu = (accu >> 1)^self.c
            else:
                accu = (accu >> 1)
            Data = (Data >> 1)
        return accu
 
    def makeCrcTable(self):
        self.crc_table = [0 for i in range(256)]
        for index in range(256):
            self.crc_table[index] = self.innerLoop(index)
        return self.crc_table

    def calc_crc_ccitt(self, b):
        crc = self.crc
        self.crc = ((crc >> 8) & 255)^(self.crc_table[(crc^b) & 255])

    def invert_crc(self):
        print('Before inverting: %i, %s'%(self.crc, hex(self.crc)))
        self.crc = self.crc^int('ffff', base=16)
        (i, r) = divmod(self.crc, 256)
        self.crc = 256*r + i
        print('After inverting: %i, %s'%(self.crc, hex(self.crc)))
        return self.crc

    def do_calc(self, src):
        # '\xFF\x01\x00\x47' (Standard G-poll on channel 255) Result should be 6b 55 = 27477
        # '\xFF\x01\x00' (Response to G-poll on channel 255) Result should be E7 19 = 59161
        # '\x1F\x00\x1E\x19' (Response on channel 31) Result is 1E 19 = 7705
        self.crc = int('ffff', base=16)
        ba = bytearray(src.replace(' ','').decode('hex'))
        for b in ba:
            self.calc_crc_ccitt(b)

        # Return the inverted results
        s = '%04s'%(hex(self.invert_crc())[2:])
        s = s.replace(' ','0')
        return s

