#!/usr/bin/env python3
import socket as sk
import time


sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

server_address = ('localhost', 10000)
message = 'Questo è il corso di ?'

try:
    print ('sending "%s"' % message)
    time.sleep(2)
    sent = sock.sendto(message.encode(), server_address)

    print('waiting to receive from')
    data, server = sock.recvfrom(4096)
    time.sleep(2)
    print ('received message "%s"' % data.decode('utf8'))
except Exception as info:
    print(info)
finally:
    print ('closing socket')
    sock.close()
