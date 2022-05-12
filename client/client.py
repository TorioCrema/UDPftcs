#!/usr/bin/env python3
import socket as sk
import time

def recFromServer(socket):
    received, server = socket.recvfrom(4096)
    data = received.decode('utf8')
    print(data)


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

    server_address = ('localhost', 10000)
    message = 'first message'

    while True:
        try:
            print (f'sending "{message}"')
            sent = sock.sendto(message.encode(), server_address)

            print('waiting for server response\n')
            data, server = sock.recvfrom(4096)
            received = data.decode('utf8')
            print(received)
        except Exception as info:
            print(info)

        sent = sock.sendto("ls".encode(), server_address)
        recFromServer(sock)       
        break

    print ('closing socket')
    sock.close()
    


