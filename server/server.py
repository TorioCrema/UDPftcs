import socket as sk
import os
from math import ceil

PACKSIZE = 8192
FILE_DIR = "./files/"

class ClientConnection:
    def __init__(self, sock, address):
        self.sock = sock
        self.address = address

    def send(self, toSend):
        sock.sendto(toSend.encode(), address)

    def recv(self):
        data, address = self.sock.recvfrom(PACKSIZE)
        return data.decode(), address

sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

server_address = ('localhost', 10000)
print ('\n\r starting up on %s port %s' % server_address)
sock.bind(server_address)

while True:
    print('\n\r waiting to receive message...')
    data, address = sock.recvfrom(PACKSIZE)
    clientConn = ClientConnection(sock, address)

    print('received %s bytes from %s' % (len(data), address))
    command = data.decode('utf8')
    print(command)
    
    
    if command == 'ls':
        print("Sending ACK")
        clientConn.send("ACK")
        files = os.scandir(path = FILE_DIR)
        response = 'Available files:\n'
        for entry in files:
            if entry.is_file:
                response += entry.name + "\n"
        clientConn.send(response)
    elif command.split()[0] == "get":
        try:
            name = FILE_DIR + command.split()[1]
            with open(name, "r") as requestedFile:
                response = requestedFile.read()
            segmentNumber = 1
            responseSize = len(response.encode())
            if responseSize > PACKSIZE:
                segmentNumber = ceil(responseSize / PACKSIZE)
        except:
            clientConn.send("Invalid command")
            continue

        clientConn.send("ACK")
        clientConn.send(f"{segmentNumber}")

        with open(name, "r") as requestedFile:
            responseList = []
            for i in range(segmentNumber):
                responseList.append(requestedFile.read(PACKSIZE))
        for i in range(segmentNumber):
            print(f"Sending package number {i}/{segmentNumber}", end='\r')
            clientConn.send(str(i))
            data, address = sock.recvfrom(PACKSIZE)
            assert i == int(data)
            clientConn.send(responseList[i])
    elif command.split()[0] == "put":
        clientConn.send("ACK")
        requestedFile = command.split()[1]
        print(f"Starting download of {requestedFile}")
        with open(FILE_DIR + requestedFile, "w") as newFile:
            data, address = clientConn.recv()
            packNum = int(data)
            for i in range(packNum):
                data, address = clientConn.recv()
                assert i == int(data)
                clientConn.send(str(i))
                data, address = clientConn.recv()
                newFile.write(data)
                print(f"Received package number {i}/{packNum}", end="\r")
        print(f"Downloaded {requestedFile} file from client.")
    else:
        response = 'Available commands:'
        response += '\n'
        response += 'ls -> lists all files available for download'
        response += "\n"
        response += "get <fileName> -> Download file"
        response += "\n"
        response += "put <fileName> -> Upload file"
        response += "\n"
        clientConn.send(response)


    