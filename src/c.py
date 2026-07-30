import socket

UDP_IP = "172.20.10.6"
UDP_PORT=5005
MESSAGE= "funfou"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MESSAGE.encode('utf-8'), (UDP_IP, UDP_PORT))