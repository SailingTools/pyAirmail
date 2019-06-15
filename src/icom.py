import serial
import time
from icom_programmer import IcomProgrammer


class radioController():
    
    def __init__(self):
        try:
            self.ser = serial.Serial(
                port='/dev/icom',
                baudrate=4800,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE, 
                stopbits=serial.STOPBITS_ONE, 
                timeout=10
            )
        except:
            self.ser = None

    def do_checksum(self, payload):
        ba = bytearray()
        cs = 0
        ba.extend(payload)
        for b in ba:
            cs = cs ^ b
        return format(cs, '02x')

    def write_sentence(self, payload, get_response=True):
        checksum = self.do_checksum(payload)
        command = "$" + payload + "*" + checksum.upper()
        #print("#  Command:  " + command)
        if self.ser:
            self.ser.write(command + "\r\n")
            if get_response:
                response = self.ser.readline()
                #print("#  Response: " + response[:-2])
                return response
        return ''

    def is_remote(self):
        r = radio.write_sentence('PICOA,90,08,REMOTE,')
        if 'ON' in r:
            return True
        else:
            return False

    def getFrequency(self):
        return float(radio.write_sentence('CCFSI,,,,').split(',')[1])/10.0

    def start_radio(self):
        self.close(); self.open()
        self.write_sentence("STARTUP", get_response=False)
        time.sleep(5)

    def restart_radio(self):
        self.close(); time.sleep(7);
        self.open();
        self.write_sentence("STARTUP", get_response=False)
        time.sleep(1);

    def remote(self, on):
        if on:
            self.write_sentence("PICOA,90,08,REMOTE,ON")
        else:
            self.write_sentence("PICOA,90,08,REMOTE,OFF")
        return None

    def setFrequency(self, freq):
        """
        m = USB, o = AM, q = AFS, s = AFS, t = AFS, w = AFS, x = CW
        0 = Power Level (?)
        """
        print('Changing frequency: %.01f'%(float(freq/10.0)))
        self.write_sentence("CCFSI,%06i,%06i,m,0"%(freq,freq))

    def close(self):
        self.ser.close()

    def stop_radio(self):
        self.ser.close()

    def open(self):
        self.ser.open()


class radioController706(IcomProgrammer):
    
    def __init__(self, ser = None):
        # Set the radio 
        self.radio_id = 0x58

        if ser is None:
            self.serial = None
            self.baud_rate = '19200'
            self.port = '/dev/icom'
            success = self.init_serial()
            if not success:
                raise Exception('Serial connection not established')
            '''
            ser = serial.Serial(
                port='/dev/icom',
                baudrate=4800,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE, 
                stopbits=serial.STOPBITS_ONE, 
                timeout=10
            )
            self.serial = ser
            '''
        else:
            self.serial = ser
        



###############

radio = radioController()
