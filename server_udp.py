import sys
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication
from server_common import *
from server_udp_fft2rd import RDWindow
from server_udp_fft2ra import RAOpenGLWindow

def unitsgen(np_dtype='uint16', endian='big'):
    def units(data):
        return bytes_to_np_array(data, np.dtype(np_dtype), '>' if endian == 'big' else '<')
    return units

def rd_values_adjust(img):
    return np.fft.fftshift(img, 1)

def ra_values_adjust(img):
#    This function must return an array of integer values in the range [0, 255] because that's the
#    kind of data configured to be sent to the GPU, since OpenGL is used for Range-Angle display
    scalars = img / (2**16 - 1)
    levels = np.round(scalars * 255).clip(0, 255).astype(np.uint8)
    return levels

UDP_IP = "127.0.0.1"
UDP_PORT = 4098
IMAGE_SIZE = [256, 32]
PACKET_SIZE = 1026
PACKET_DISCARD_BYTES = 2
UNIT_SIZE = 2 # bytes per data unit
UNIT_INTENSITY_FUNC = unitsgen('uint16', 'big')

class MultiWindow(object):

    def __init__(self, windows):
        self.windows = windows

    def show(self):
        for w in self.windows:
            w.show()

class MainApp(AbstractApp):
    def __init__(self, rd_values_adjust_func, ra_values_adjust_func):
        app = QApplication(sys.argv)
        window = MultiWindow([RDWindow(IMAGE_SIZE, scalex=4, scaley=1), RAOpenGLWindow(IMAGE_SIZE)])
        window.windows[0].resize(512, 768)
        window.windows[0].setWindowTitle("2D FFT Range-Doppler")
        window.windows[1].resize(768, 512)
        window.windows[1].setTitle("2D FFT Range-Angle")
        receiver = Receiver(UDP_IP, UDP_PORT, IMAGE_SIZE, PACKET_SIZE, PACKET_DISCARD_BYTES, UNIT_SIZE, UNIT_INTENSITY_FUNC)
        super().__init__(app, window, receiver)
        self.current_window = 0
        self.rd_values_adjust_func = rd_values_adjust_func
        self.ra_values_adjust_func = ra_values_adjust_func

    def update_data(self):
#        if not (hasattr(self.window.windows[0], 'imv') and hasattr(self.windows.windows[1], 'texture')):
#            return

        win = self.window.windows[self.current_window]
        if self.current_window == 0:
            img = self.rd_values_adjust_func(self.worker.data)
            win.imv.getImageItem().setImage(img)
        elif self.current_window == 1:
            img = self.ra_values_adjust_func(self.worker.data)
            win.texture.setData(QtGui.QOpenGLTexture.Luminance, QtGui.QOpenGLTexture.UInt8, img)
        win.update()

        self.current_window += 1
        self.current_window %= len(self.window.windows)

if __name__ == "__main__":
    pg.setConfigOption('imageAxisOrder', 'row-major')
    pg.setConfigOptions(antialias=True)
    app = MainApp(rd_values_adjust, ra_values_adjust)
    sys.exit(app.run())
