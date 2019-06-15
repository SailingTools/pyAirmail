#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ***************************************************************************
# *   Copyright (C) 2018, Paul Lutus                                        *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU General Public License for more details.                          *
# *                                                                         *
# *   You should have received a copy of the GNU General Public License     *
# *   along with this program; if not, write to the                         *
# *   Free Software Foundation, Inc.,                                       *
# *   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.             *
# ***************************************************************************

import os, sys, re, operator, datetime, time, subprocess
import atexit, serial, platform, zipfile

VERSION = 1.6

# NOTE: Versions 1.6 and above are written in Python 3

# set this flag to True for development work

DEBUG = True

class IcomUtilities:

  def __init__(self):

    # User configuration table
    self.radio_configurations = {
      'IC-706' : ('IC-706',('general_hf','marine_hf','marine_vhf_wx','marine_vhf_short','E')),
      'IC-7000-Boat' : ('IC-7000',('general_hf','marine_hf','marine_vhf_wx','general_vhf_uhf','emergency_beacon','marine_vhf_long','family_radio_service','cb','E')),
      'IC-7000-Home' : ('IC-7000',('general_hf','marine_hf','marine_vhf_wx','general_vhf_uhf','emergency_beacon','marine_vhf_long','family_radio_service','cb','vhf_repeaters_long','E')),
      'IC-746' : ('IC-746',('general_hf','marine_hf','marine_vhf_wx','marine_vhf_short','vhf_repeaters_short','E')),
      'IC-756Pro' : ('IC-756Pro',('general_hf','marine_hf','E')),
      'IC-R8500' : ('IC-R8500',('general_hf','marine_hf','marine_vhf_wx','marine_vhf_long','general_vhf_uhf','emergency_beacon','family_radio_service','cb','public_service','vhf_repeaters_long','E'))
    }

    # change these if needed
    
    self.baud_rate = '19200'

    # Linux: ttyS0, ttyS1 for conventional serial interfaces
    # or ttyUSB0, ttyUSB1 for USB serial adaptors
    self.linux_port = 'ttyUSB0'

    # Windows: COM1, COM2, etc
    self.windows_port = 'COM1'

    # 'use_ods_files' if True uses OpenOffice spreadsheet files
    # located in 'frequency_data_ods' subdirectory
    # otherwise uses CSV files
    # located in 'frequency_data_csv' subdirectory
    self.use_ods_files = True

    self.icom_codes = {
      # Ham Radios:
      'IC-703'          : 0x68,
      'IC-706'          : 0x4e,
      'IC-706MKIIG'     : 0x58,
      'IC-718'          : 0x5e,
      'IC-725'          : 0x28,
      'IC-726'          : 0x30,
      'IC-728'          : 0x38,
      'IC-729'          : 0x3a,
      'IC-735'          : 0x04,
      'IC-736'          : 0x40,
      'IC-746'          : 0x56,
      'IC-746Pro'       : 0x66,
      'IC-751'          : 0x1c,
      'IC-756Pro'       : 0x5c,
      'IC-756Pro-II'    : 0x64,
      'IC-756Pro-III'   : 0x6e,
      'IC-761'          : 0x1e,
      'IC-765'          : 0x2c,
      'IC-775'          : 0x46,
      'IC-781'          : 0x26,
      'IC-970'          : 0x2e,
      'IC-7000'         : 0x70,
      'IC-7200'         : 0x76,
      'IC-7600'         : 0x7a,
      'IC-7700'         : 0x74,
      'IC-7800'         : 0x6a,
      # Receivers
      'IC-R71'          : 0x1A,
      'IC-R72'          : 0x32,
      'IC-R75'          : 0x5a,
      'IC-R7000'        : 0x08,
      'IC-R7100'        : 0x34,
      'IC-R8500'        : 0x4a,
      'IC-R9000'        : 0x2a,
      # Marine Radios
      'M-7000Pro'       : 0x02,
      'M-710'           : 0x01,
      'M-710RT'         : 0x03,
      'M-802'           : 0x08,
      'Any'             : 0x00 # (any Icom marine radio)
    }
    
    self.memory_label_sizes = {
      'IC-R75' : 8,
      'IC-R8500' : 8,
      'IC-746' : 9,
      'IC-746Pro' : 9,
      'IC-756Pro' : 10,
      'IC-756Pro-II' : 10,
      'IC-756Pro-III' : 10,
      'IC-7000' : 9,
      'IC-7200' : 9,
      'IC-7600' : 9,
      'IC-7700' : 9,
      'IC-7800' : 9
    }
    
    self.bank_sizes = {
      'IC-R8500' : 40,
      'IC-7000' : 99,
      'IC-7200' : 99,
      'IC-7600' : 99,
      'IC-7700' : 99,
      'IC-7800' : 99
    }

    self.modes = {
      'lsb'  : 0,
      'usb'  : 1,
      'am'   : 2,
      'cw'   : 3,
      'rtty' : 4,
      'fm'   : 5,
      'wfm'  : 6
    }
    
    self.ods_directory = 'frequency_data_ods'
    
    self.fcsv_directory = 'frequency_data_csv'
    
    self.ftsv_directory = 'frequency_data_tsv'
    
    self.fhtml_directory = 'frequency_data_html'
    
    self.rcsv_directory = 'radio_csv_tables'
    
    self.rtsv_directory = 'radio_tsv_tables'
    
    self.html_directory = 'radio_html_tables'
    
    self.pdf_directory = 'radio_pdf_files'
    
    for d in (self.ods_directory,self.html_directory,self.fhtml_directory,self.fcsv_directory,self.ftsv_directory,self.rcsv_directory,self.rtsv_directory,self.pdf_directory):
      if(not os.path.exists(d)):
        os.makedirs(d)
      

    self.field_names = (
      'Bank','Mem','Name','MemTag','Mode','RxFreq',
      'TxFreq','RxTone','TxTone','Comment',
      'Place','Call','Sponsor','Region'
    )

    self.field_hash = {}
    for n,name in enumerate(self.field_names):
      self.field_hash[name] = n

    self.css_style_block = """
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
      <style type=\'text/css\'>
        body * {
          font-family: Verdana, Tahoma, Helvetica, Arial;
        }
        table {
          border-collapse:collapse;
        }
        td {
          border:1px solid #808080;
          padding-right:4px;
          padding-left:4px;
          white-space: nowrap;
        }
        th {
          border:1px solid #808080;
          padding-right:4px;
          padding-left:4px;
          background:#ffffe0;
          font-weight: bold;
          text-align: center;
        }
        .cell0 { background:#eff1f1; }
        .cell1 { background:#f8f8f8; }
      </style>"""

    self.xml_tab_str = '  '

  def debug_print(self,s,linefeed = True):
    if(DEBUG):
      sys.stderr.write(s)
      if(linefeed): sys.stderr.write('\n')

  def read_file(self,path):
    with open(path) as f:
      return f.read()

  def write_file(self,path,data):
    with open(path,'w') as f:
      f.write(data)

  def wrap_tag(self,tag,data,mod = ''):
    if(len(mod) > 0): mod = ' ' + mod
    return '<%s%s>\n%s\n</%s>\n' % (tag,mod,data,tag)

  def beautify_xhtml(self,data,otab = 0):
    tab = otab
    xml = []
    data = re.sub('\n+','\n',data)
    for record in data.split('\n'):
      record = record.strip()
      outc = len(re.findall('</|/>',record))
      inc = len(re.findall('<\w',record))
      net = inc - outc
      tab += min(net,0)
      xml.append((self.xml_tab_str * tab) + record)
      tab += max(net,0)
    if(tab != otab):
      self.debug_print('Error: tag mismatch: %d\n' % tab)
    return '\n'.join(xml) + '\n'

  def array_to_xhtml(self,radio_name,array):
    table = ''
    row_num = 0
    for record in array:
      row = ''
      for field in record:
        field = field.strip()
        # strip quotes
        field = re.sub('"','',field)
        # replace blank field with &nbsp;
        field = re.sub('^$','&nbsp;',field)
        row += self.wrap_tag(('td','th')[row_num == 0],field)
      row_num += 1
      mod = ('class="cell%d"' % (row_num % 2),'')[row_num == 0]
      table+= self.wrap_tag('tr',row,mod)
    table = self.wrap_tag('table',table, 'cellpadding="0" cellspacing="0" border="0"')
    footer = 'Created using '
    footer += self.wrap_tag('a','IcomProgrammer','href=\"http://arachnoid.com/IcomProgrammer\"')
    footer += ' &mdash; copyright &copy; 2018,  P. Lutus'
    table += self.wrap_tag('p',footer)
    dtime =  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z").strip()
    title = radio_name + ' &mdash; ' + dtime
    page = self.wrap_tag('div',table,'align="center"')
    page = self.wrap_tag('body',page)
    head = self.wrap_tag('title',title)
    page = self.wrap_tag('head',head + self.css_style_block) + page
    page = self.wrap_tag('html',page)
    page = self.beautify_xhtml(page)
    return page

  def format_floats(self,record):
    output = []
    for field in record:
      try:
        v = float(field)
        field = '%08.4f' % v
      except:
        None
      output.append(field)
    return output

  def array_from_csv_file(self,fn):
    path = os.path.join(self.fcsv_directory,fn + '.csv')
    data = self.read_file(path)
    output = []
    for line in re.split('\n',data):
      line = line.strip()
      if(len(line) > 0):
        line = re.sub('^"(.*?)"$','\\1',line,1)
        record = re.split('","',line)
        record = self.format_floats(record)
        output.append(record)
    return output

  def encode_write_xsv_file(self,path,array,token,delim):
    output = ''
    for record in array:
      output += delim + token.join(record) + delim + '\n'
    self.write_file(path,output)
    
  def encode_write_pdf_file(self,radio_name,html_data,pdf_path):
    #try:
    if True:
      dtime =  datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z").strip()
      p = subprocess.Popen(
        ['wkhtmltopdf', '--header-left',
        radio_name,'--header-right', dtime,
        '-q','--footer-center', '[page]/[toPage]',
        '-', '-'],stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE)
      stdoutdata, stderrdata = p.communicate(bytearray(html_data,'utf-8'))
      self.write_file(pdf_path,str(stdoutdata))
    #except Exception as e:
    #  sys.stderr.write('Error: %s (possibly no pdf converter present)\n' % e)

  def encode_write_xhtml_file(self,radio_name,path,array):
    page = self.array_to_xhtml(radio_name,array)
    self.write_file(path,page)
    return page

  def add_records_to_array(self,records,array):
    if(len(array) == 0):
      array.append(self.field_names)
      self.used_array = [False for i in self.field_names]
    name_hash = {}
    header = records.pop(0)
    for field in self.field_names:
      if(field in header):
        name_hash[field] = operator.indexOf(header,field)
    for record in records:
      output = ['' for s in self.field_names]
      for name in self.field_names:
        if(name in name_hash):
          s = record[name_hash[name]].strip()
          if(len(s) > 0):
            n = self.field_hash[name]
            output[n] = s
            self.used_array[n] = True
      array.append(output)

  def remove_empty_fields_from_array(self,array):
    output = []
    for record in array:
      newrec = []
      for n,used in enumerate(self.used_array):
        if(used): newrec.append(record[n])
      output.append(newrec)
    return output

class OdsToArray:

  def extract_simple(self,data,tag):
    return re.findall('(?s)<%s[^/|>]*?>(.*?)</%s>' % (tag,tag),str(data))

  def extract_complex(self,data,tag):
    output = []
    # must capture open and closed tags, both with repeat specifiers
    array = re.findall('(?s)(<%s[^/>]*?/>)|(<%s[^/>]*?>.*?)</%s>' % (tag,tag,tag),data)
    for tup in array:
      for datum in tup:
        n = 1
        if re.search('table:number-columns-repeated',datum):
          # get column-repeat value
          sn = re.sub('.*table:number-columns-repeated=\"(\d+)\".*','\\1',datum)
          n = int(sn)
        if re.search('/>',datum):
          # repeat empty columns
          if(n > 1):
            n = min(n,self.record_sz - len(output))
          for i in range(n):
            output.append('')
        else:
          # now strip out the residual table tag
          datum = re.sub('<table.*?>','',datum)
          if(len(datum) > 0):
            # repeat data columns
            for i in range(n):
              output.append(datum)
    return output

  def extract_record(self,row):
    output = []
    n = 0
    fields = self.extract_complex(row,'table:table-cell')
    for field in fields:
      content = self.extract_simple(field,'text:p')
      if(len(content) > 0):
        n += 1
        output.append(content[0])
      else:
        output.append('')
    if(n > 0):
      self.record_sz = max(len(output),self.record_sz)
      return output
    else:
      return None

  def array_from_ods_file(self,fn):
    path = os.path.join(self.ods_directory,fn + '.ods')
    zf = zipfile.ZipFile(path)
    with zf.open('content.xml') as f:
      data = f.read()
    zf.close()
    array = []
    self.record_sz = 0
    sheets = self.extract_simple(data,'office:spreadsheet')
    for sheet in sheets:
      tables = self.extract_simple(sheet,'table:table')
      for table in tables:
        rows = self.extract_simple(table,'table:table-row')
        for row in rows:
          record = self.extract_record(row)
          if(record and len(record) > 0):
            record = self.format_floats(record)
            array.append(record)
    return array

class IcomIO:

  def __init__(self):
    self.serial = False
    self.opsys = platform.system()
    if(re.search('(?i)linux',self.opsys)):
      self.port = '/dev/' + self.linux_port
    elif(re.search('(?i)windows',self.opsys)):
      self.port = self.windows_port
    else:
      sys.stderr.write('Error: Cannot identify operating system: "%s".\n' % self.opsys)
      sys.exit(0)
    self.set_defaults(0)
    # Register exit function
    atexit.register(self.exit)

  def set_defaults(self,banksize):
    self.banksize = banksize
    self.current_vfo = -1
    self.mem_bank = -1
    self.mem_loc = -1
    self.split = False

  def exit(self):
    self.close_serial()
    self.debug_print('IcomIO exit')

  def close_serial(self):
    if(self.serial):
      self.serial.flush()
      self.serial.close()
    self.serial = False

  def init_serial(self,force = False):
    if(force or not self.serial):
      try:
        self.close_serial()
        self.serial = serial.Serial(
          self.port,
          self.baud_rate,
          parity = serial.PARITY_NONE,
          timeout = 1000,
          rtscts = 0
        )
        self.serial.flushOutput()
        self.serial.flushInput()
      except:
        self.serial = False
    return self.serial != False

  def read_radio_n(self,n):
    self.debug_print('Read Radio count %d: ' % n,False)
    count = 0
    reply = []
    while(count < n):
      s = self.serial.read(1)
      c = 0
      if(len(s) > 0):c = s[0]
      reply.append(c)
      self.debug_print('%02x ' % c,False)
      count += 1
    self.debug_print('')
    return reply

  def render_list_as_hex(self,data):
    s = '[ '
    for c in data:
      s += '%02x ' % c
    s += ']'
    return s;
    
  def read_radio_s(self):
    self.debug_print('Read Radio until 0xfd: ',False)
    count = 0
    reply = []
    c = 0
    while(c != 0xfd):
      s = self.serial.read(1)
      c = 0
      if(len(s) > 0):c = s[0]
      reply.append(c)
      self.debug_print('%02x ' % c,False)
      count += 1
    self.debug_print('')
    return reply

  def write_radio(self,com):
    self.debug_print('Write Radio: ',False)
    for c in com:
      self.debug_print('%02x ' % c,False)
      self.serial.write(bytes([c]))
    self.debug_print('')
    # discard echo reply
    self.read_radio_n(len(com))

  def read_radio_response(self):
    reply = self.read_radio_n(6)
    return reply[4] == 0xfb # meaning no errors

  def convert_bcd(self,n,count):
    n = int(n)
    bcd = []
    for i in range(count):
      bcd.append((n % 10) | ((n//10) % 10) << 4)
      n //= 100
    return bcd

  def send_com_core(self,c,data = False):
    com = [0xfe,0xfe,self.radio_id,0xe0,c]
    if(data):
      com += data
    com.append(0xfd)
    self.write_radio(com)
    return com
    
  def send_com(self,c,data = False):
    com = self.send_com_core(c,data)
    print("DONE SENDING COME CORE")
    #reply = self.read_radio_n(len(com))
    #import pdb;pdb.set_trace()
    #r = (reply[4] == 0xfb)
    r = read_radio_response()
    print("DONE READING RESPINSE")
    if(not r):
      err = 'Error: ' + self.render_list_as_hex(com)
      self.debug_print(err)
    return r

  def set_memory_mode(self):
    self.debug_print('set memory mode')
    self.send_com(0x08)

  def set_vfo(self,n):
    self.debug_print('set vfo: %d' % n)
    if(self.current_vfo != n):
      self.current_vfo = n
      self.send_com(0x07) # select VFO mode (required for IC-756)
      self.send_com(0x07,[ 0xd0 + n ]) # select VFO main/sub (required for IC-756)
      return self.send_com(0x07,[ n ]) # select VFO

  # 01.24.2018 default force = True to avoid
  # a default setting of split mode
  def set_split(self,split, force = True):
    if(force or self.split != split):
      c = (0,1)[split]
      self.debug_print('set split mode: %d' % c)
      r = self.send_com(0x0f,[c])
      if(r):
        self.split = split
      return r

  def set_memory_bank(self,mb):
    if(mb != self.mem_bank):
      self.mem_bank = mb
      bcd = self.convert_bcd(mb,1)
      #bcd.reverse()
      bcd = [ 0xa0 ] + bcd
      self.debug_print('set memory bank: %d : %s' % (mb,self.render_list_as_hex(bcd)))
      return self.send_com(0x08,bcd)
    else:
      return True
      
  def set_memory_addr(self,m,banksize):
    # the R8500 uses zero-based indexing
    # all other radios use 1-based
    offset = (1,0)[self.r8500]
    if(banksize != 0):
      ma = m % banksize
      mb = m / banksize
      r = self.set_memory_bank(mb+offset)
      if(not r):
        self.debug_print('fail set memory bank: %d' % (mb+offset))
        return False
      bcd = self.convert_bcd(ma+offset,2)
      bcd.reverse()
    else:
      bcd = self.convert_bcd(m+offset,2)
      bcd.reverse()
    self.debug_print('set memory address: %d %s' % (m,self.render_list_as_hex(bcd)))
    r = self.send_com(0x08,bcd)
    # user feedback
    sys.stdout.write('.')
    sys.stdout.flush()
    return r
    
  def pad_char(self,s,length,c):
    while(len(s) < length):
      s += c
    return s
    
  def set_memory_name(self,mem,banksize,mem_tag,radio_tag):
    self.debug_print('setting memory tag %s' % mem_tag)
    if(radio_tag in self.memory_label_sizes):
      tag_len = self.memory_label_sizes[radio_tag]
    else:
      self.debug_print('Fail mem tag on radio %s' % radio_tag)
      return
    # the R8500 uses zero-based indexing
    # all other radios use 1-based
    offset = (1,0)[self.r8500]
    # special read com for the IC-R8500
    read_com = (0,1)[self.r8500]
    if(banksize != 0):
      ma = mem % banksize
      mb = mem / banksize
      mab = self.convert_bcd(ma+offset,2)
      mab.reverse()
      mbb = self.convert_bcd(mb+offset,1)
      mbb.reverse()
      self.send_com_core(0x1a, [read_com] + mbb + mab)    
    else:
      mab = self.convert_bcd(mem+offset,2)
      mab.reverse()
      self.send_com_core(0x1a, [read_com] + mab)
    result = self.read_radio_s()
    if(result):
      rl = len(result)
      if(rl > tag_len):
        # limit tag size to max
        mem_tag = mem_tag[:tag_len]
        # extend tag length for short tags
        mem_tag = self.pad_char(mem_tag,tag_len,' ')
        # convert from chars to numbers
        mem_tag = [ord(c) for c in mem_tag]
        delta = tag_len+1
        for n in range(tag_len):
          result[-(delta - n)] = mem_tag[n]
        # to transmit the received data block,
        # must change order of sender and recipient
        temp = result[2]
        result[2] = result[3]
        result[3] = temp
        # for the IC-R8500, change com
        if(self.r8500):
          result[5] = 0
        self.write_radio(result)
        r = self.read_radio_response()
        if(not r):
          err = 'Error in set memory name: ' + self.render_list_as_hex(result)
          self.debug_print(err)
        return r
          
      else:
        self.debug_print('wrong reply length in set memory name: %d %s' % (rl,self.render_list_as_hex(result)))
    else:
      self.debug_print('fail from read_radio_s')
        

  def set_vfo_freq(self,n):
    f = (n * 1.0e6) + 0.5
    self.debug_print('set VFO freq: %f' % f)
    n = int(f)
    bcd = self.convert_bcd(n,5)
    self.send_com(0x05,bcd)

  def set_vfo_tone(self,n,f):
    f = (f * 10.0) + 0.5
    f = int(f)
    bcd = self.convert_bcd(f,2)
    bcd.reverse()
    bcd = [n] + bcd
    self.send_com(0x1b,bcd)

  def set_vfo_mode(self,s):
    self.debug_print('set VFO mode: %s %d' % (s,self.modes[s]))
    self.send_com(0x06,[self.modes[s]])

  def get_field_by_name(self,record,name):
    r = record[self.field_hash[name]].strip()
    if(len(r) == 0):
      r = False
    else:
      try:
        r = float(r)
      except:
        None
    return r

  def program_radio(self,array,radio_id,banksize,radio_tag,erase_unused = False):
    if(not self.init_serial()):
      sys.stderr.write('Error: cannot open serial interface, aborting.\n')
      return
    self.radio_id = radio_id
    self.r8500 = (radio_tag == 'IC-R8500')
    has_split = self.set_split(False,True)
    self.debug_print('has_split : %s' % has_split)
    self.current_vfo = -1
    self.set_vfo(0)
    base = 0
    start_time = time.time()
    total = 0
    for mm,record in enumerate(array[1:]):
      # if(mm > 10): break
      total += 1
      mem = base + mm
      mode = self.get_field_by_name(record,'Mode')
      mem_tag = self.get_field_by_name(record,'MemTag')
      rxf = self.get_field_by_name(record,'RxFreq')
      txf = self.get_field_by_name(record,'TxFreq')
      rxt = self.get_field_by_name(record,'RxTone')
      txt = self.get_field_by_name(record,'TxTone')
      if(rxf and mode): # minimum required
        self.set_memory_addr(mem,banksize)
        if(has_split):
          # make sure that a transmit frequency is
          # specified and nonzero, to prevent
          # a default split mode
          if(txf and txf > 0):
            self.set_split(True)
            self.set_vfo(1)
            self.set_vfo_freq(txf)
            self.set_vfo_mode(mode)
            if(txt): # transmit repeater tone
              self.send_com(0x16,[ 0x42,0x1 ]) # repeater tone on
              self.set_vfo_tone(0,txt)
          else:
            self.set_split(False)
        if(has_split):
          self.set_vfo(0)
        self.set_vfo_freq(rxf)
        self.set_vfo_mode(mode)
        if(rxt): # receiver tone squelch
          self.send_com(0x16,[ 0x43,0x1 ]) # tone squelch on
          self.set_vfo_tone(1,rxt)
        else:
          self.send_com(0x16,[ 0x43,0x0 ]) # tone squelch off
        self.debug_print('write VFO to memory')
        self.send_com(0x09) # write mem
        if(mem_tag):
          self.set_memory_name(mem,banksize,mem_tag,radio_tag)
        # break
    self.set_memory_mode()
    if(erase_unused):
      r = True
      # point to first unused location
      m = base + len(array[1:])
      while(r):
        total += 1
        r = self.set_memory_addr(m,banksize)
        if(r):
          self.debug_print('reset memory adress: %d' % m)
          self.send_com(0x0b)
        m += 1
    self.set_memory_addr(base,banksize)
    self.close_serial()
    end_time = time.time()
    dt = end_time - start_time
    per_trans_ms = dt * 1000 / total 
    print('\n\nTotal time: %f seconds for %d transactions, %f milliseconds per transaction\n' % (end_time - start_time,total, per_trans_ms))

class IcomProgrammer(IcomUtilities,IcomIO,OdsToArray):

  def __init__(self):
    IcomUtilities.__init__(self)
    IcomIO.__init__(self)

  def process_radio(self,tag,commit = True):
    s = ('Creating Lists for','Programming')[commit]
    print('%s %s ...' % (s,tag))
    erase_unused = False
    master_array = []
    if(not tag in self.radio_configurations):
      sys.stderr.write('Error: no configuration for "%s".\n' % tag)
    else:
      config = self.radio_configurations[tag]
      radio_model = config[0]
      if(not radio_model in self.icom_codes):
        sys.stderr.write('Error: no hex code for radio model "%s".\n' % radio_model)
      else:
        hex_code = self.icom_codes[radio_model]
        if(radio_model in self.bank_sizes):
          bank_size = self.bank_sizes[radio_model]
        else:
          bank_size = 0
        for path in config[1]:
          if(path == 'E'):
            erase_unused = True
          else:
            if(self.use_ods_files):
              records = self.array_from_ods_file(path)
            else:
              records = self.array_from_csv_file(path)
            self.add_records_to_array(records,master_array)
        self.used_array[1] = True
        self.used_array[0] = (bank_size > 0)
        for i,record in enumerate(master_array[1:]):
          if(bank_size > 0):
            bank = i / bank_size
            n = i % bank_size
            record[0] = '%02d' % bank
            record[1] = '%02d' % n
          else:
            record[1] = '%02d' % (i + 1)
        if(commit):
          self.program_radio(master_array,hex_code,bank_size,radio_model,erase_unused)
        master_array = self.remove_empty_fields_from_array(master_array)
        self.encode_write_xsv_file(os.path.join(self.rcsv_directory,tag + '.csv'),master_array,'","','"')
        self.encode_write_xsv_file(os.path.join(self.rtsv_directory,tag + '.tsv'),master_array,'\t','')
        html_path = os.path.join(self.html_directory,tag + '.html')
        html_page = self.encode_write_xhtml_file(tag,html_path,master_array)
        self.encode_write_pdf_file(tag,html_page,os.path.join(self.pdf_directory,tag + '.pdf'))

  def create_radio_lists(self):
    for key in sorted(self.radio_configurations.keys()):
      self.process_radio(key,False)
      
  def create_xsv_files(self):
    files = os.listdir(self.ods_directory)
    for fn in files:
      if(re.match('(?i).*\\.ods$',fn)):
        fn = re.sub('(?i)(.*)\.ods$','\\1',fn)
        records = self.array_from_ods_file(fn)
        self.encode_write_xsv_file(os.path.join(self.fcsv_directory,fn + '.csv'),records,'","','"')
        self.encode_write_xsv_file(os.path.join(self.ftsv_directory,fn + '.tsv'),records,'\t','')
        html_path = os.path.join(self.fhtml_directory,fn + '.html')
        self.encode_write_xhtml_file(fn,html_path,records)
    
  def process(self):
    menu = []
    radio_list = []
    for key in sorted(self.radio_configurations.keys()):
      radio_list.append(key)
      menu.append('Program ' + key)
    menu.append('Create All Radio Frequency Lists')
    menu.append('Create All CSV/TSV Frequency Lists')
    menu.append('Quit')
    while True:
      print('Options:')
      for n,item in enumerate(menu):
        print('    %d: %s' % (n+1,item))
      lm = len(menu)
      reply = input('Select (1 - %d): ' % lm)
      #reply = sys.stdin.readline()
      tag = False
      try:
        x = int(reply)
      except:
        x = -1
      if(x < 1 or x > lm):
        print('Pleae enter a valid number.')
      else:
        if(x == lm):
          sys.exit(0)
        elif(re.search('Radio Frequency',menu[x-1])):
          self.create_radio_lists()
        elif(re.search('CSV/TSV',menu[x-1])):
          self.create_xsv_files()
        else:
          tag = radio_list[x-1]
          if(tag):
            self.process_radio(tag)

#ip = IcomProgrammer().process()
