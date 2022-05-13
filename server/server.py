import socket as sk
import time
import os

PACKSIZE = 4096

class ClientConnection:
    def __init__(self, sock, address):
        self.sock = sock
        self.address = address

    def send(self, toSend):
        sock.sendto(toSend.encode(), address)
        # print(f"Sent: {toSend}")

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
        print("Sending ACK")
        clientConn.send("ACK")
        files = os.scandir(path = '.')
        response = 'Available files:\n'
        for entry in files:
            if entry.is_file:
                response += entry.name + "\n"
        clientConn.send(response)
    elif command.split()[0] == "get":
        try:
            name = command.split()[1]
            with open(name, "r") as requestedFile:
                response = requestedFile.read()
            segmentNumber = 1
            responseSize = len(response.encode())
            if responseSize > 4096:
                segmentNumber = responseSize // PACKSIZE
        except:
            clientConn.send("Invalid command")

        clientConn.send("ACK")
        clientConn.send(f"{segmentNumber}")

        with open(name, "r") as requestedFile:
            responseList = []
            for i in range(segmentNumber):
                responseList.append(requestedFile.read(PACKSIZE))
        for i in range(segmentNumber):
            print(f"Sending package number {i}...")
            clientConn.send(responseList[i])
    else:
        response = 'Available commands:'
        response += '\n'
        response += 'ls -> lists all files available for download'
        response += "\n"
        response += "get <fileName> -> Download file"
        response += "\n"
        clientConn.send(response)


    