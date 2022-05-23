import json
import pickle
import socket as sk
import os
from math import ceil
from typing import Tuple

PACKSIZE = 8192
BUFF = 16384
FILE_DIR = "./files/"

class ClientConnection:
    def __init__(self, sock: sk.socket, address):
        self.sock = sock
        self.address = address

    def send(self, toSend: bytes):
        sock.sendto(toSend, address)

    def recv(self) -> Tuple:
        data, address = self.sock.recvfrom(BUFF)
        return data, address

sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

server_address = ('localhost', 10000)
print ('\n\r starting up on %s port %s' % server_address)
sock.bind(server_address)

while True:
    print('\n\r waiting to receive message...')
    data, address = sock.recvfrom(BUFF)
    clientConn = ClientConnection(sock, address)

    print('received %s bytes from %s' % (len(data), address))
    command = data.decode('utf8')
    print(command)
    
    
    if command == 'ls':
        print("Sending ACK")
        clientConn.send("ACK".encode())
        files = os.scandir(path = FILE_DIR)
        response = 'Available files:\n'
        for entry in files:
            if entry.is_file:
                response += entry.name + "\n"
        clientConn.send(response.encode())
    elif command.split()[0] == "get":
        try:
            name = FILE_DIR + command.split()[1]
            with open(name, "rb") as requestedFile:
                response = requestedFile.read()
            segmentNumber = 1
            responseSize = len(response)
            if responseSize > PACKSIZE:
                segmentNumber = ceil(responseSize / PACKSIZE)
        except:
            clientConn.send("Invalid command".encode())
            continue

        clientConn.send("ACK".encode())
        clientConn.send(str(segmentNumber).encode())
        with open(name, "rb") as requestedFile:
            responseList = []
            for i in range(segmentNumber):
                responseList.append({"index": i, "bytes": requestedFile.read(PACKSIZE)})
        for i in range(segmentNumber):
            print(f"Sending package number {i}/{segmentNumber}", end='\r')
            clientConn.send(pickle.dumps(responseList[i]))
        # send end of file
        clientConn.send(pickle.dumps({"index": -1, "bytes": b"0"}))
        # check missing packets
        data, address = clientConn.recv()
        data = data.decode()
        print(f"data={data}")
        while data != "-1":
            clientConn.send(pickle.dumps(responseList[int(data)])) # invalid literal for int???
            data, address = clientConn.recv()
            data = data.decode()
    elif command.split()[0] == "put":
        clientConn.send("ACK".encode())
        requestedFile = command.split()[1]
        print(f"Starting download of {requestedFile}")
        with open(FILE_DIR + requestedFile, "wb") as newFile:
            data, address = clientConn.recv()
            data = data.decode()
            packNum = int(data)
            for i in range(packNum):
                data, address = clientConn.recv()
                data = data.decode()
                assert i == int(data)
                clientConn.send(str(i).encode())
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
        clientConn.send(response.encode())


    