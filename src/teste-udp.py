import socket
import select

UDP_IP = "0.0.0.0"
UDP_PORT1 = 5005
UDP_PORT2 = 5006

sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1.bind((UDP_IP, UDP_PORT1))

sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.bind((UDP_IP, UDP_PORT2))

sockets_list = [sock1, sock2]

while True:
    # O select aguarda até que QUALQUER um dos sockets receba dados
    readable, _, _ = select.select(sockets_list, [], [])

    for s in readable:
        data, addr = s.recvfrom(1024)
        porta = s.getsockname()[1]
        print(f"Recebido da porta {porta}: {data.decode('utf-8')}")