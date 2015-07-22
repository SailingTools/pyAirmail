import serial
import time

"""
Note that HF Radio must be on for the modem to respond.
"""

def readto(ser, end="cmd: ", line=''):
    if not ser.inWaiting():
        return None
    while not line[-5:] == end:
        line += ser.read(1)
    lines = line.split('\r')
    print('\n'.join(lines))
    return lines

if __name__ == "__main__":
    ser=serial.Serial(port='/dev/modemSCS', baudrate=57600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10, xonxoff=True)
    #ser=serial.Serial(port='\\.\COM8', baudrate=57600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10, xonxoff=True)
    #ser.open()

    ser.write('\r')
    lines = readto(ser)

    ser.write('mycall VJN4455\r')   
    lines = readto(ser)
    ser.write('tones 4\r')
    lines = readto(ser)
    ser.write('chobell 0\r')
    lines = readto(ser)
    ser.write('lfignore 1\r')
    lines = readto(ser)

    # Now make the connection to the station
    ser.write("c ZKN2SM\r")     # Connect to NIUE for now
    line = ""
    line += ser.read(1);line;

    ser.write("FQ\r")

    # Disconnect from the station
    ser.write("d\r")
	
    ser.close()

"""
  fprintf(fp, "\r\n");
  while ((line = wl2kgetline(fp)) != NULL) {
    printf("%s\n", line);
    if (strstr(line, "cmd:")) {
      fprintf(fp, "mycall %s\r", cfg.mycall);
      printf("mycall %s\n", cfg.mycall);
      fprintf(fp, "tones 4\r");
      printf("tones 4\n");
      fprintf(fp, "chobell 0\r");
      printf("chobell 0\n");
      fprintf(fp, "lfignore 1\r");
      printf("lfignore 1\n");
      break;
    }
    fprintf(fp, "\r\n");
  }
  if (line == NULL) {
    fprintf(stderr, "Connection closed by foreign host.\n");
    exit(EXIT_FAILURE);
  }

#if 0
  while ((line = wl2kgetline(fp)) != NULL) {
    printf("%s\n", line);
    if (strstr(line, "Mycall:")) {
      break;
    }
  }
  if (line == NULL) {
    fprintf(stderr, "Connection closed by foreign host.\n");
    exit(EXIT_FAILURE);
  }
#endif

  while ((line = wl2kgetline(fp)) != NULL) {
    printf("%s\n", line);
    if (strstr(line, "cmd:")) {
      fprintf(fp, "c %s\r", cfg.targetcall);
      printf("c %s\n", cfg.targetcall);
      break;
    }
  }
  if (line == NULL) {
    fprintf(stderr, "Connection closed by foreign host.\n");
    exit(EXIT_FAILURE);
  }

ser.close()
"""