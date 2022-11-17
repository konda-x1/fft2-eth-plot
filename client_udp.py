import socket
import random
import time
import numpy as np

def msg(num_points=256):
    return random.getrandbits(num_points*4*8).to_bytes(num_points*4, 'big')

def msg2(num_bytes = 1024):
    return random.getrandbits(num_bytes * 8).to_bytes(num_bytes, 'big')

def to_bytes(real, imag):
    return real.to_bytes(2, 'big', signed=True) + imag.to_bytes(2, 'big', signed=True)

def sendmsg(bytes, udp_ip="127.0.0.1", udp_port=4098):
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(b'\x00\x00' + bytes, (udp_ip, udp_port))
    
def sendgrad(udp_ip="127.0.0.1", udp_port=4098):
    absrow = 0
    for packet in range(8):
        bytes = b''
        for row in range(32):
            for col in range(16):
#                val = round(16383 / (255 + 7) * (asrow + row + col))
#                val = round(16383 / (256*8) * (8 * (absrow + row) + col))
                val = round((2**16-1) * (absrow + row) / 255 * col / 15)
                bytes += val.to_bytes(2, 'big')
        sendmsg(bytes, udp_ip, udp_port)
        absrow += 32

def send_from_file(file_name, dtype, bytes_per_packet=1024, udp_ip="127.0.0.1", udp_port=4098):
    arr = np.loadtxt(file_name, dtype=dtype).byteswap()
    data = arr.tobytes()
    assert len(data) % bytes_per_packet == 0
    num_packets = len(data) // bytes_per_packet
    for i in range(num_packets):
        packet_data = data[i*bytes_per_packet:(i+1)*bytes_per_packet]
        sendmsg(packet_data, udp_ip, udp_port)

def sendnum(real, imag, udp_ip="127.0.0.1", udp_port=4098):
    sendmsg(to_bytes(real, imag), udp_ip, udp_port)

if __name__ == "__main__":
    while True:
        sendmsg(msg())
#        time.sleep(0.00625)

