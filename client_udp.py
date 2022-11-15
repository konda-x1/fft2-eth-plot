import socket
import random
import time

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
            for col in range(8):
#                val = round(16383 / (255 + 7) * (absrow + row + col))
#                val = round(16383 / (256*8) * (8 * (absrow + row) + col))
                val = round(16383 * (absrow + row) / 255 * col / 7)
                bytes += 2 * val.to_bytes(2, 'big')
        sendmsg(bytes, udp_ip, udp_port)
        absrow += 32

def sendnum(real, imag, udp_ip="127.0.0.1", udp_port=4098):
    sendmsg(to_bytes(real, imag), udp_ip, udp_port)

if __name__ == "__main__":
    while True:
        sendmsg(msg())
#        time.sleep(0.00625)

