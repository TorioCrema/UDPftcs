from functools import partial
import pickle
import signal
import socket as sk
import os
from config import FILE_DIR, BUFF, PACKSIZE
from math import ceil
import sys
from typing import List
import ClientConnection as cc


def intSignalHandler(signal, frame, socket: sk.socket):
    print("Closing socket.")
    socket.close()
    print("Exiting")
    sys.exit(0)


def getFileLen(fileName: str) -> int:
    fileName = FILE_DIR + fileName
    with open(fileName, "rb") as file:
        response = file.read()
    packNum = 1
    responseSize = len(response)
    if responseSize > PACKSIZE:
        packNum = ceil(responseSize / PACKSIZE)
    return packNum


def getResponseList(fileName: str, segmentNumber: int) -> List:
    with open(FILE_DIR + fileName, "rb") as file:
        responseList = []
        for i in range(segmentNumber):
            toSend = {"index": i, "bytes": file.read(PACKSIZE)}
            responseList.append(toSend)
    return responseList


def recvFile(clientConn: cc.ClientConnection, data: dict) -> List:
    while data['index'] != -1:
        packList.insert(data["index"], data["bytes"])
        data, address = clientConn.recv()
        data = pickle.loads(data)


def writeFile(fileName: str, packList: List):
    with open(FILE_DIR + fileName, "wb") as file:
        for pack in packList:
            file.write(pack)


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    intSignalHandler = partial(intSignalHandler, socket=sock)
    signal.signal(signal.SIGINT, intSignalHandler)

    server_address = ('localhost', 10000)
    print(f'Starting up on {server_address[0]} port {server_address[1]}')
    sock.bind(server_address)

    while True:
        print('waiting to receive message...')
        data, address = sock.recvfrom(BUFF)
        clientConn = cc.ClientConnection(sock, address)
        dataLen = len(data)
        print(f'received {dataLen} bytes from {address}')
        command = data.decode('utf8')
        print(command)

        if command == 'ls':
            print("Sending ACK")
            clientConn.send("ACK")
            files = os.scandir(path=FILE_DIR)
            response = 'Available files:\n'
            for entry in files:
                if entry.is_file:
                    response += entry.name + "\n"
            clientConn.send(response.encode())
        elif command.split()[0] == "get":
            name = command.split()[1]
            try:
                segmentNumber = getFileLen(name)
            except IOError:
                clientConn.send("Invalid command")
                continue

            clientConn.send("ACK")
            clientConn.send(str(segmentNumber))

            responseList = getResponseList(name, segmentNumber)
            for i in range(segmentNumber):
                print(f"Sending package number {i}/{segmentNumber}", end='\r')
                clientConn.send(pickle.dumps(responseList[i]))
            # send end of file
            clientConn.send(pickle.dumps({"index": -1, "bytes": b"0"}))

        elif command.split()[0] == "put":
            clientConn.send("ACK")
            requestedFile = command.split()[1]
            print(f"Starting download of {requestedFile}")
            try:
                data, address = clientConn.recv()
                data = data.decode()
                packNum = int(data)
                data, address = clientConn.recv()
                data = pickle.loads(data)
                packList = recvFile(clientConn, data)
                writeFile(requestedFile, packList)
                print(f"{requestedFile} downloaded from client correctly.")
                if len(packList) != packNum:
                    print("Error while downloading file, aborting operation.")
                    clientConn.send("Error")
                    os.remove(os.path.join(FILE_DIR, requestedFile))

                else:
                    clientConn.send("ACK")
            except sk.timeout or IOError:
                print("Error while downloading file, aborting operation.")
                clientConn.send("Error")
                os.remove(os.path.join(FILE_DIR, requestedFile))
        else:
            response = 'Available commands:\n'
            response += 'ls -> lists all files available for download\n'
            response += "get <fileName> -> Download file\n"
            response += "put <fileName> -> Upload file\n"
            clientConn.send(response)
