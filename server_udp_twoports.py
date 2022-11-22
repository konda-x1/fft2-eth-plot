import sys
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication
from server_common import *
from server_udp_fft2rd import RDWindow
from server_udp_fft2ra import RAOpenGLWindow
from scipy.interpolate import interp2d

RD_UPSCALE_INTERPOLATE_FACTOR=4
RD_SCALEX=4
RD_SCALEY=1

def unitsgen(np_dtype='uint16', endian='big'):
    def units(data):
        return bytes_to_np_array(data, np.dtype(np_dtype), '>' if endian == 'big' else '<')
    return units

def rd_values_adjust(img):
    shifted = np.fft.fftshift(img, 1)
    xcoords = RD_SCALEX * RD_UPSCALE_INTERPOLATE_FACTOR * np.arange(shifted.shape[1])
    ycoords = RD_SCALEY * RD_UPSCALE_INTERPOLATE_FACTOR * np.arange(shifted.shape[0])
    interp_func = interp2d(xcoords, ycoords, shifted, kind='linear')
    interpolated_real = interp_func(np.arange(RD_SCALEX * RD_UPSCALE_INTERPOLATE_FACTOR * shifted.shape[1]), np.arange(RD_SCALEY * RD_UPSCALE_INTERPOLATE_FACTOR * shifted.shape[0]))
    interpolated = np.round(interpolated_real).clip(0, 2**16-1).astype(np.uint16)
    return interpolated

def ra_values_adjust(img):
#    This function must return an array of integer values in the range [0, 255] because that's the
#    kind of data configured to be sent to the GPU, since OpenGL is used for Range-Angle display
    scalars = img / (2**16 - 1)
    levels = np.round(scalars * 255).clip(0, 255).astype(np.uint8)
    return levels

UDP_IP = "127.0.0.1"
UDP_PORT_RD = 4098
UDP_PORT_RA = 4099
IMAGE_SIZE = [256, 32]
PACKET_SIZE = 1026
PACKET_DISCARD_BYTES = 2
UNIT_SIZE = 2 # bytes per data unit
UNIT_INTENSITY_FUNC = unitsgen('uint16', 'big')

class MainApp(object):
    def __init__(self, rd_values_adjust_func, ra_values_adjust_func):
        self.app = QApplication(sys.argv)
        self.window_rd = RDWindow([RD_UPSCALE_INTERPOLATE_FACTOR * RD_SCALEY * IMAGE_SIZE[0], RD_UPSCALE_INTERPOLATE_FACTOR * RD_SCALEX * IMAGE_SIZE[1]], image_data_process_func=rd_values_adjust_func)
        self.window_rd.resize(512, 768)
        self.window_rd.setWindowTitle("2D FFT Range-Doppler")
        self.window_ra = RAOpenGLWindow(IMAGE_SIZE, image_data_process_func=ra_values_adjust_func)
        self.window_ra.resize(768, 512)
        self.window_ra.setTitle("2D FFT Range-Angle")

        self.receiver_rd = Receiver(UDP_IP, UDP_PORT_RD, IMAGE_SIZE, PACKET_SIZE, PACKET_DISCARD_BYTES, UNIT_SIZE, UNIT_INTENSITY_FUNC)
        self.receiver_ra = Receiver(UDP_IP, UDP_PORT_RA, IMAGE_SIZE, PACKET_SIZE, PACKET_DISCARD_BYTES, UNIT_SIZE, UNIT_INTENSITY_FUNC)

        self.thread_rd, self.worker_rd = make_thread_worker(self.receiver_rd, self.window_rd.update_image)
        self.thread_ra, self.worker_ra = make_thread_worker(self.receiver_ra, self.window_ra.update_image)

    def run(self):
        self.window_rd.show()
        self.window_ra.show()
        self.thread_rd.start()
        self.thread_ra.start()
        return self.app.exec_()

if __name__ == "__main__":
    pg.setConfigOption('imageAxisOrder', 'row-major')
    pg.setConfigOptions(antialias=True)
    app = MainApp(rd_values_adjust, ra_values_adjust)
    sys.exit(app.run())
