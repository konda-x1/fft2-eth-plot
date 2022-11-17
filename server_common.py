import sys
import socket
import numpy as np
from PyQt5.QtCore import QObject, QThread, pyqtSignal

def bytes_to_np_array(data, dtype, byteorder):
    return np.frombuffer(data, dtype=dtype.newbyteorder(byteorder)).astype(int)

def make_gradient(height, width):
    vals = []
    for row in range(height):
        for col in range(width):
            vals.append(row / (height-1) * col / (width - 1))
    levels = np.round(np.array(vals) * 255).astype(np.uint8)
    imat = levels.reshape([height, width])
    return imat
    
class Receiver(object):
    def __init__(self, udp_ip, udp_port, image_size, packet_size, packet_discard_bytes, unit_size, unit_intensity_func, packet_buffer_size=None):
        self.effective_packet_size = packet_size - packet_discard_bytes
        if len(image_size) != 2:
            raise ValueError("image_size must be of length 2")
        if self.effective_packet_size % unit_size != 0:
            raise ValueError(f"Effective packet size ({self.effective_packet_size}) is not divisible by unit size ({unit_size})")
        units_per_packet = self.effective_packet_size // unit_size
        units_per_image = image_size[0] * image_size[1]
        if units_per_image % units_per_packet != 0:
            raise ValueError(f"Number of data units composing an image ({units_per_image}) is not divisible by the number of data units per packet ({units_per_packet})")
        
        if packet_buffer_size is None:
            packet_buffer_size = 2 * self.effective_packet_size
        self.packet_buffer_size = packet_buffer_size
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((udp_ip, udp_port))
        self.image_size = image_size
        self.packet_size = packet_size
        self.packet_discard_bytes = packet_discard_bytes
        self.unit_size = unit_size
        self.unit_intensity_func = unit_intensity_func
        self.packet_buffer_size = packet_buffer_size
        self.image_num_packets = units_per_image // units_per_packet
        print(f"{self.__class__.__name__}: Expecting {self.image_num_packets} packets with {self.packet_size} bytes ({self.effective_packet_size} effective bytes) to form a single image.")
    
    def recv_packet_data(self):
        data = self.sock.recv(self.packet_buffer_size)
        if len(data) != self.packet_size:
            raise ValueError(f"Invalid packet byte length {len(data)}, {self.packet_size} bytes expected")
        return data[self.packet_discard_bytes:]
    
    def safe_recv_packet_data(self):
        try:
            data = self.recv_packet_data()
        except ValueError as e:
            print(f"Ignoring invalid packet due to error \"{str(e)}\" and assuming a zeroed-out block of data.")
            data = bytes(self.effective_packet_size)
        return data
    
    def recv_image_data(self):
        units = np.concatenate([ self.unit_intensity_func(self.safe_recv_packet_data()) for _ in range(self.image_num_packets) ])
#        levels = np.round(scalars * 255.0).clip(0, 255).astype(np.uint8)
#        return levels
        return units
    
    def next_image(self):
        return self.recv_image_data().reshape(self.image_size)


class Worker(QObject):
    update = pyqtSignal()
    def __init__(self, receiver):
        global IMAGE_SIZE
        super().__init__()
        self.r = receiver

    def run(self):
        while True:
            self.data = self.r.next_image()
            self.update.emit()

class AbstractApp(object):
    def __init__(self, qapp, window, receiver):
        self.app = qapp
        self.receiver = receiver
        self.window = window

        self.thread = QThread()
        self.worker = Worker(self.receiver)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.update.connect(self.update_data)

    def update_data(self):
        raise NotImplementedError

    def run(self):
        self.window.show()
        self.thread.start()
        self.app.exec_()

