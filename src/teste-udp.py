import socket

UDP_IP = "0.0.0.0"
UDP_PORT = 5005
UDP_PORT2 = 5006

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.bind((UDP_IP, UDP_PORT2))

while True:
    data, addr = sock.recvfrom(1024)
    data2, addr2 = sock2.recvfrom(1024)
    print(data, data2)