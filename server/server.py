from functools import partial
import pickle
import signal
import socket as sk
import os
from math import ceil
import sys
from typing import Tuple

PACKSIZE = 8192
BUFF = 16384
FILE_DIR = "./files/"


def intSignalHandler(signal, frame, socket: sk.socket):
    print("Closing socket.")
    socket.close()
    print("Exiting")
    sys.exit(0)


class ClientConnection:
    def __init__(self, sock: sk.socket, address):
        self.sock = sock
        self.address = address

    def send(self, toSend: bytes):
        sock.sendto(toSend, address)

    def recv(self) -> Tuple:
        data, address = self.sock.recvfrom(BUFF)
        return data, address


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    intSignalHandler = partial(intSignalHandler, socket=sock)
    signal.signal(signal.SIGINT, intSignalHandler)

    server_address = ('localhost', 10000)
    print(f'Starting up on {server_address[0]} port {server_address[1]}')
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
            files = os.scandir(path=FILE_DIR)
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
            except IOError:
                clientConn.send("Invalid command".encode())
                continue

            clientConn.send("ACK".encode())
            clientConn.send(str(segmentNumber).encode())
            with open(name, "rb") as file:
                responseList = []
                for i in range(segmentNumber):
                    toSend = {"index": i, "bytes": file.read(PACKSIZE)}
                    responseList.append(toSend)
            for i in range(segmentNumber):
                print(f"Sending package number {i}/{segmentNumber}", end='\r')
                clientConn.send(pickle.dumps(responseList[i]))
            # send end of file
            clientConn.send(pickle.dumps({"index": -1, "bytes": b"0"}))
        elif command.split()[0] == "put":
            clientConn.send("ACK".encode())
            requestedFile = command.split()[1]
            print(f"Starting download of {requestedFile}")
            packNum = -1
            packList = []
            while len(packList) != packNum:
                try:
                    data, address = clientConn.recv()
                    data = data.decode()
                    packNum = int(data)
                    data, address = clientConn.recv()
                    data = pickle.loads(data)
                    while data['index'] != -1:
                        packList.insert(data["index"], data["bytes"])
                        data, address = clientConn.recv()
                        data = pickle.loads(data)
                    with open(FILE_DIR + requestedFile, "wb") as newFile:
                        for packData in packList:
                            newFile.write(packData)
                    print(f"{requestedFile} downloaded from client correctly.")
                    clientConn.send("ACK".encode())
                except sk.timeout:
                    print("Error while downloading file, aborting operation.")
                    clientConn.send("Error".encode())
                    os.remove(os.path.join(FILE_DIR, requestedFile))
                    break
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
