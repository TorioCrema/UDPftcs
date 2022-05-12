import socket as sk
import time
import os

sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

server_address = ('localhost', 10000)
print ('\n\r starting up on %s port %s' % server_address)
sock.bind(server_address)

while True:
    print('\n\r waiting to receive message...')
    data, address = sock.recvfrom(4096)

    print('received %s bytes from %s' % (len(data), address))
    command = data.decode('utf8')
    print (command)
    
    
    if command == 'ls':
        files = os.scandir(path = '.')
        response = 'Available files:\n'
        for entry in files:
            if entry.is_file:
                response += entry.name
    else:
        response = 'Available commands:'
        response += '\n'
        response += 'ls -> lists all files available for download'

    sent = sock.sendto(response.encode(), address)
    print ('sent %s bytes back to %s' % (sent, address))
