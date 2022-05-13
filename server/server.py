import socket as sk
import time
import os

PACKSIZE = 4096

class ClientConnection:
    def __init__(self, sock, address):
        self.sock = sock
        self.address = address

    def send(toSend):
        sock.sendto(toSend.encode, address)

sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

server_address = ('localhost', 10000)
print ('\n\r starting up on %s port %s' % server_address)
sock.bind(server_address)

while True:
    print('\n\r waiting to receive message...')
    data, address = sock.recvfrom(4096)
    clientConn = ClientConnection(sock, address)

    print('received %s bytes from %s' % (len(data), address))
    command = data.decode('utf8')
    print(command)
    
    
    if command == 'ls':
        files = os.scandir(path = '.')
        response = 'Available files:\n'
        for entry in files:
            if entry.is_file:
                response += entry.name + "\n"
    elif command.split()[0] == "get":
        try:
            name = command.split()[1]
            with open(name, "r") as requestedFile:
                response = requestedFile.read()
            segmentNumber = 1
            responseSize = response.encode().__sizeof__
            if responseSize > 4096:
                segmentNumber = responseSize / 4096
        except:
            clientConn.send("Invalid command")

        clientConn.send("ACK")
        sock.sendto(f"{segmentNumber}".encode(), address)

        with open(name, "r") as requestedFile:
            responseList = []
            for i in range(segmentNumber):
                responseList.append(requestedFile.read(PACKSIZE))
        for i in range(segmentNumber):
            print(f"Sending package number {i}...")
            clientConn.send(responseList[i])
            time.sleep(0.1)
        
        

    else:
        response = 'Available commands:'
        response += '\n'
        response += 'ls -> lists all files available for download'
        response += "\n"
        response += "get <fileName> -> Download file"
        response += "\n"

    sent = sock.sendto(response.encode(), address)
    print ('sent %s bytes back to %s' % (sent, address))

    