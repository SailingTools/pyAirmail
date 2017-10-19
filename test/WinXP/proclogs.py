
def get_channel(fname, channel=31, keywords=['WRITE', 'READ']):
    f = open(fname, 'r')
    lines = f.readlines()
    f.close()

    c = str(bytearray([channel])).encode('hex').upper()
    cheader = 'AA AA %s'%(c)
    outlines = []
    for line in lines:
        s = ''

        procline = False
        if cheader in line:
            for k in keywords:
                if k in line:
                    procline = True
                    if k == 'WRITE':
                        s += '>>'
                    if k == 'READ':
                        s += '<<'

        if not procline:
            continue

        d = line.split(cheader)[1:]
        d = ''.join(d).strip()

        d = d.split(' ')[2:-2]
        
        s += ''.join(d).decode('hex')
        outlines.append(s)

    return outlines        
