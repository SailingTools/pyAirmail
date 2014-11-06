import sys
import os
import socket
import tempfile
import subprocess
import shutil
import email
import struct
import time
import re

sys.path.insert(0, "..")

FBB_BLOCK_HDR = 1
FBB_BLOCK_DAT = 2
FBB_BLOCK_EOF = 4

FBB_BLOCK_TYPES = { FBB_BLOCK_HDR : "header",
                    FBB_BLOCK_DAT : "data",
                    FBB_BLOCK_EOF : "eof",
                    }

def update_crc(c, crc):
    for _ in range(0,8):
        c <<= 1

        if (c & 0400) != 0:
            v = 1
        else:
            v = 0
            
        if (crc & 0x8000):
            crc <<= 1
            crc += v
            crc ^= 0x1021
        else:
            crc <<= 1
            crc += v

    return crc & 0xFFFF

def calc_checksum(data):
    checksum = 0
    for i in data:
        checksum = update_crc(ord(i), checksum)

    checksum = update_crc(0, checksum)
    checksum = update_crc(0, checksum)

    return checksum

def run_lzhuf(cmd, data):
    cwd = tempfile.mkdtemp()

    f = file(os.path.join(cwd, "input"), "wb")
    f.write(data)
    f.close()

    kwargs = {}
    if subprocess.mswindows:
        su = subprocess.STARTUPINFO()
        su.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        su.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = su

    if os.name == "nt":
        lzhuf = "LZHUF_1.EXE"
    elif os.name == "darwin":
        raise Exception("Not supported on MacOS")
    else:
        lzhuf = "lzhuf"

    lzhuf_path = os.path.abspath(os.path.join("libexec", lzhuf))
    shutil.copy(os.path.abspath(lzhuf_path), cwd)
    run = [lzhuf_path, cmd, "input", "output"]
    
    print "Running %s in %s" % (run, cwd)

    ret = subprocess.call(run, cwd=cwd, **kwargs)
    print "LZHUF returned %s" % ret
    if ret:
        return None

    f = file(os.path.join(cwd, "output"), "rb")
    data = f.read()
    f.close()

    return data

def run_lzhuf_decode(data):
    return run_lzhuf("d", data[2:])

def run_lzhuf_encode(data):
    lzh = run_lzhuf("e", data)
    lzh = struct.pack("<H", calc_checksum(lzh)) + lzh
    return lzh

class WinLinkMessage:
    def __init__(self, header=None):
        self.__name = ""
        self.__content = ""
        self.__usize = self.__csize = 0
        self.__id = ""
        self.__type = "P"

        if header:
            fc, self.__type, self.__id, us, cs, off = header.split()
            self.__usize = int(us)
            self.__csize = int(cs)

            if int(off) != 0:
                raise Exception("Offset support not implemented")

    def __decode_lzhuf(self, data):
        return run_lzhuf_decode(data)

    def __encode_lzhuf(self, data):
        return run_lzhuf_encode(data)

    def recv_exactly(self, s, l):
        data = ""
        while len(data) < l:
            data += s.recv(l - len(data))

        return data

    def read_from_socket(self, s):
        data = ""

        i = 0
        while True:
            print "Reading at %i" % i
            t = ord(self.recv_exactly(s, 1))

            if chr(t) == "*":
                msg = s.recv(1024)
                raise Exception("Error getting message: %s" % msg)

            if t not in FBB_BLOCK_TYPES.keys():
                i += 1
                print "Got %x (%c) while reading %i" % (t, chr(t), i)
                continue

            print "Found %s at %i" % (FBB_BLOCK_TYPES.get(t, "unknown"), i)
            size = ord(self.recv_exactly(s, 1))
            i += 2 # Account for the type and size

            if t == FBB_BLOCK_HDR:
                header = self.recv_exactly(s, size)
                self.__name, offset, foo = header.split("\0")
                print "Name is `%s' offset %s\n" % (self.__name, offset)
                i += size
            elif t == FBB_BLOCK_DAT:
                print "Reading data block %i bytes" % size
                data += self.recv_exactly(s, size)
                i += size
            elif t == FBB_BLOCK_EOF:
                cs = size
                for i in data:
                    cs += ord(i)
                if (cs % 256) != 0:
                    print "Ack! %i left from cs %i" % (cs, size)
                
                break

        print "Got data: %i bytes" % len(data)
        self.__content = self.__decode_lzhuf(data)
        if self.__content is None:
            raise Exception("Failed to decode compressed message")
        
        if len(data) != self.__csize:
            print "Compressed size %i != %i" % (len(data), self.__csize)
        if len(self.__content) != self.__usize:
            print "Uncompressed size %i != %i" % (len(self.__content),
                                                  self.__usize)

    def send_to_socket(self, s):
        data = self.__lzh_content

        # filename \0 length(0) \0
        # From: http://www.f6fbb.org/protocole.html#version1
        # The offset is also transmitted in ascii and specifies the offset at which the 
        # data should be inserted in the file (in case of a fragmented file). 
        # In the version 5.12, this parameter is not utilized and is always equal to zero.
        #header = self.__name + "\x00" + chr(len(data) & 0xFF) + "\x00"
        header = self.__name + "\x00" + "0" + "\x00"
        s.send(struct.pack("BB", FBB_BLOCK_HDR, len(header)) + header)

        cs = 0
        while data:
            chunk = data[:128]
            data = data[128:]

            for i in chunk:
                cs += ord(i)

            s.send(struct.pack("BB", FBB_BLOCK_DAT, len(chunk)) + chunk)

        # Checksum, mod 256, two's complement
        cs = (~cs & 0xFF) + 1
        s.send(struct.pack("BB", FBB_BLOCK_EOF, cs))

    def get_content(self):
        return self.__content

    def set_content(self, content, name="message"):
        self.__name = name
        self.__content = content
        self.__lzh_content = self.__encode_lzhuf(content)
        self.__usize = len(self.__content)
        self.__csize = len(self.__lzh_content)

    def get_id(self):
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_proposal(self):
        return "FC %s %s %i %i 0" % (self.__type, self.__id,
                                     self.__usize, self.__csize)

class WinLinkCMS:
    def __init__(self, callsign):
        self._callsign = callsign
        self.__messages = []
        self._conn = None

    def __ssid(self):
        return "[AirMail-3.3.081-B2FHIM$]"

    def _send(self, string):
        print "  -> %s" % string
        self._conn.send(string + "\r")

    def __recv(self):
        resp = ""
        while not resp.endswith("\r\n"):
            resp += self._conn.recv(1)

            if re.findall("Login \(.*\):", resp) or re.findall("Password \(.*\):", resp):
                resp += ">\r\n"
                break

        resp = resp.strip()
        print "  <- %s" % resp
        return resp

    def _isComment(self, line):
        return line.startswith(";")

    def _isTerminal(self, line):
        if line.endswith(">"):
            return True
        elif line.startswith("F>"):
            return True
        elif line.startswith("FQ"):
            return True
        elif line.startswith("FS"):
            return True
        elif line.startswith("*** Error"):
            return True
        return False

    def _recv(self):
        lines = []
        line = ";"
        while self._isComment(line) or (not self._isTerminal(line)):
            line = self.__recv()
            if not self._isComment(line):
                lines.append(line)
        return "\r".join(lines)

    def _send_ssid(self):
        self._send(self.__ssid())

    def __get_list(self):
        self._send("FF")

        msgs = []
        reading = True
        while reading:
            resp = self._recv()
            for l in resp.split("\r"):
                if l.startswith("FC"):
                    print "Creating message for %s" % l
                    msgs.append(WinLinkMessage(l))
                elif l.startswith("F>"):
                    reading = False
                    break
                elif l.startswith("FQ"):
                    reading = False
                    break
                elif not l:
                    pass
                else:
                    print "Invalid line: %s" % l
                    raise Exception("Conversation error (%s while listing)" % l)

        return msgs

    def get_messages(self):
        #self._connect()
        #self._login()
        self.__messages = self.__get_list()

        if self.__messages:
            self._send("FS %s" % ("Y" * len(self.__messages)))

            for msg in self.__messages:
                print "Getting message..."
                try:
                    msg.read_from_socket(self._conn)
                except Exception, e:
                    raise
                    #print e
                    
            self._send("FQ")
        else:
            print("No messages.")

        #self._disconnect()

        return len(self.__messages)

    def get_message(self, index):
        return self.__messages[index]

    def send_messages(self, messages):
        #if len(messages) != 1:
        #    raise Exception("Sorry, batch not implemented yet")

        #self._connect()
        #self._login()

        cs = 0
        for msg in messages:
            p = msg.get_proposal()
            for i in p:
                cs += ord(i)
            cs += ord("\r")
            self._send(p)

        cs = ((~cs & 0xFF) + 1)
        self._send("F> %02X" % cs)
        resp = self._recv()

        if not resp.startswith("FS"):
            raise Exception("Error talking to server: %s" % resp)

        fs, accepts = resp.split()
        if len(accepts) != len(messages):
            raise Exception("Server refused some of my messages?!")

        for msg in messages:
            print "Sending message...",
            msg.send_to_socket(self._conn)
            print "Done"

        resp = self._recv()
        #self._disconnect()

        return 1

class WinLinkTelnet(WinLinkCMS):
    def __init__(self, callsign, server="pop3.sailmail.com", port=50001):
        self.__server = server
        self.__port = port
        WinLinkCMS.__init__(self, callsign)

    def _connect(self):
        class sock_file:
            def __init__(self):
                self.__s = 0

            def read(self, len):
                return self.__s.recv(len)

            def write(self, buf):
                return self.__s.send(buf)

            def connect(self, spec):
                return self.__s.connect(spec)

            def close(self):
                self.__s.close()

        self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._conn.connect((self.__server, self.__port))

    def _disconnect(self):
        self._conn.close()
        print("Connection closed")

    def _login(self):
        resp = self._recv()
        if not resp.startswith("Login"):
            raise Exception("Conversation error (never saw login)")

        self._send(self._callsign)
        resp = self._recv()
        if not resp.startswith("Password"):
            raise Exception("Conversation error (never saw password)")

        self._send("Tuuletar")
        resp = self._recv()

        self._send_ssid()

class WinLinkRMSPacket(WinLinkCMS):
    def __init__(self, callsign, remote, agw):
        self.__remote = remote
        self.__agw = agw
        WinLinkCMS.__init__(self, callsign)

    def _connect(self):
        self._conn = agw.AGW_AX25_Connection(self.__agw, self._callsign)
        self._conn.connect(self.__remote)

    def _disconnect(self):
        self._conn.disconnect()

    def _login(self):
        resp = self._recv()
        self._send_ssid(resp)


if __name__=="__main__":
    
    # Test Telnet connection
    wl = WinLinkTelnet("VJN4455")
    print("Getting messages")
    count = wl.get_messages()
    print "%i messages" % count
    for i in range(0, count):
        print "--Message %i--\n%s\n--End--\n\n" % (i, wl.get_message(i).get_content())

    sys.exit()

    # Test RMS connection
    agwc = agw.AGWConnection("127.0.0.1", 8000, 0.5)
    wl = WinLinkRMSPacket("KK7DS", "N7AAM-11", agwc)
    count = wl.get_messages()
    print "%i messages" % count
    for i in range(0, count):
        print "--Message %i--\n%s\n--End--\n\n" % (i, wl.get_message(i).get_content())
    
    # Test create a new message:
    text = "This is a test."
    _m = """MID: 1326_VJN4455\r
Date: 2014/11/06 21:06\r
Type: Private\r
From: smtp:"Tuuletar"\r
To: smtp:"sv.tuuletar" <sv.tuuletar@gmail.com>\r
Subject: TEST TEST\r
Mbo: VJN4455\r
X-AM-RCPT: sv.tuuletar@gmail.com\r
Body: %i\r
\r
%s\r
""" % (len(text), text)

    m = WinLinkMessage()
    m.set_id("vjn4455_1234")
    m.set_content(_m, name="TEST TEST")
    wl = WinLinkTelnet("VJN4455")
    wl.send_messages([m])

