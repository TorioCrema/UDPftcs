from functools import partial
import pickle
import signal
import socket as sk
import os
from config import FILE_DIR, BUFF, PACKSIZE, COMMANDS
from math import ceil
import sys
from typing import List, Tuple
from ClientConnection import ClientConnection
from time import sleep
from hashlib import sha256


def intSignalHandler(signal, frame, socket: sk.socket):
    print("\nClosing socket.")
    socket.close()
    print("Quitting...")
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


def getLocalSha(packList: List) -> str:
    bytesList = [i['bytes'] for i in packList]
    bytesStr = b''.join(bytesList)
    return sha256(bytesStr).hexdigest()


def recvFile(clientConn: ClientConnection) -> Tuple:
    clientConn.sock.settimeout(3.0)
    data, address = clientConn.recv()
    data = data.decode()
    packNum = int(data)
    if packNum == -1:
        return packNum, [], ""
    packList = []
    while True:
        data, address = clientConn.recv()
        data = pickle.loads(data)
        if data['index'] == -1:
            break
        packList.append(data)
    packList.sort(key=lambda x: x['index'])
    return packNum, packList, data['sha']


def writeFile(fileName: str, packList: List):
    with open(FILE_DIR + fileName, "wb") as file:
        for pack in packList:
            file.write(pack['bytes'])


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    intSignalHandler = partial(intSignalHandler, socket=sock)
    signal.signal(signal.SIGINT, intSignalHandler)

    server_address = ('localhost', 10000)
    print(f'Starting up on {server_address[0]} port {server_address[1]}')
    sock.bind(server_address)

    while True:
        sock.settimeout(None)
        print('waiting to receive message...')
        data, address = sock.recvfrom(BUFF)
        clientConn = ClientConnection(sock, address)
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
                packNum = getFileLen(name)
            except IOError:
                clientConn.send("Invalid command")
                continue

            clientConn.send("ACK")
            clientConn.send(str(packNum))

            responseList = getResponseList(name, packNum)
            for i in responseList:
                print(f"Sending package {i['index']}/{packNum}", end='\r')
                clientConn.send(pickle.dumps(i))
                sleep(0.0001)
            # send file hash
            localHash = getLocalSha(responseList)
            clientConn.send(pickle.dumps({"index": -1, "sha": localHash}))

        elif command.split()[0] == "put":
            clientConn.send("ACK")
            requestedFile = command.split()[1]
            print(f"Starting download of {requestedFile}")
            try:
                packNum, packList, remoteSha = recvFile(clientConn)
                if getLocalSha(packList) != remoteSha:
                    print("Error while downloading file, aborting operation.")
                    clientConn.send("Error")
                else:
                    writeFile(requestedFile, packList)
                    print(f"{requestedFile} downloaded from client correctly.")
                    clientConn.send("ACK")
            except sk.timeout or IOError:
                print("Error while downloading file, aborting operation.")
                clientConn.send("Error")
        else:
            clientConn.send(COMMANDS)
