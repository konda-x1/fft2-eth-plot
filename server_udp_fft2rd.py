import sys
import numpy as np

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import pyqtgraph as pg

from server_common import *

def maggen(max_mag, np_dtype='uint16', endian='big'):
    def mag(data):
        units = bytes_to_np_array(data, np.dtype(np_dtype), '>' if endian == 'big' else '<')
        scalars = (units / max_mag).clip(0, 1)
        return scalars
    return mag

UDP_IP = "127.0.0.1"
UDP_PORT = 4098
IMAGE_SIZE = [256, 32]
PACKET_SIZE = 1026
PACKET_DISCARD_BYTES = 2
UNIT_SIZE = 2 # bytes per data unit
UNIT_INTENSITY_FUNC = maggen(2**16-1, 'uint16', 'big')
 
class RDWindow(QMainWindow):

    def __init__(self, image_size, scalex=1, scaley=1):
        super().__init__()

        self.imv = pg.ImageView()
        self.imv.view.invertY(False)
        self.imv.getImageItem().setTransform(QTransform().scale(scalex, scaley))
        img = make_gradient(*image_size)
        self.imv.getImageItem().setImage(img)
 
        # Set a "short rainbow" color map
        colors = [
            (0  , 0  , 255),
            (0  , 255, 255),
            (0  , 255, 0  ),
            (255, 255, 0  ),
            (255, 0  , 0  ),
        ]
        cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, len(colors)), color=colors)
        self.imv.setColorMap(cmap)
 
        self.setCentralWidget(self.imv)

class MainApp(AbstractApp):
    def __init__(self):
        app = QApplication(sys.argv)
        window = RDWindow(IMAGE_SIZE)
        window.resize(512, 768)
        window.setWindowTitle("2D FFT Range-Doppler")
        receiver = Receiver(UDP_IP, UDP_PORT, IMAGE_SIZE, PACKET_SIZE, PACKET_DISCARD_BYTES, UNIT_SIZE, UNIT_INTENSITY_FUNC)    
        super().__init__(app, window, receiver)

    def update_data(self):
        if not hasattr(self.window, 'imv'):
            return

        self.window.imv.setImage(self.worker.data)
        self.window.update()

if __name__ == "__main__":
    pg.setConfigOption('imageAxisOrder', 'row-major')
    app = MainApp()
    sys.exit(app.run())
