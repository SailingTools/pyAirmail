import numpy as np
import matplotlib.pyplot as plt
from modem import Fax

mode_amplitudes = [
0.0, 0.0, 0.0, 
0.0, 0.0, 0.0, 
0.0, 0.0, 0.0,
0.0, 0.0, 1.0,
]

def make_sin_wave(t):
    y = np.zeros(len(t))
    plt.figure()
    m = 1
    for a in mode_amplitudes:
	w = a * np.sin(t*m*np.pi/(len(t)-1))
        y = y + w
        m += 1
    	plt.plot(w)
    plt.plot(y)
    return y

def make_square_wave(t):
    f = 16
    p = 256/f
    y = ([1.0]*(p/2) + [0.0]*(p/2))*f
    plt.figure()
    plt.plot(y)
    return y

def run_test():
    plt.ion()
    t = np.arange(256)
    #y = make_sin_wave(t)
    y = make_square_wave(t)
    sp = np.fft.fft(y)
    freq = np.fft.fftfreq(t.shape[-1], d=(1.0/255))
    plt.figure()
    plt.plot(freq, sp.real, freq, sp.imag)

def plotline(data, n, xres=1800):
    plt.ion()
    st = xres*n
    plt.plot(np.array(bytearray(data[st:st+xres])))

def plotlines(data, start_line, end_line, xres=1800):
    plt.ion()
    rows = end_line-start_line
    a = np.array(bytearray(data[start_line*xres:end_line*xres]))
    a = a.reshape((rows, xres))
    plt.imshow(a, vmin=0, vmax=255, cmap='gray')
    plt.show()

if __name__ == "__main__":
    #run_test()

    plt.ion()
    f = Fax()
    f.load_data('fax_images/2015-07-28_084150.bin')

    r = bytearray('\xff'*len(f.data))
    p = np.zeros((len(f.data)/256)-1)
    for i in range((len(f.data)/256)-1):
        s = i*256
        e = s + 256
        d = f.data[s:e]
        if f.is_apt_signal(d, frequency=12):
            r[s:e] = '\x0c'*256
            p[i] = 12
        elif f.is_apt_signal(d, frequency=8):
            r[s:e] = '\x08'*256
            p[i] = 8

    f.data = r
    plt.ion()
    plt.figure()
    f.plot(show_image=True, save_image=False, save_data=False)

    plt.figure()
    plt.plot(p)

    raw_input('Press any key to quit')
