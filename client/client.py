from functools import partial
import pickle
from math import ceil
import signal
import socket as sk
import os
import sys
from typing import List, Tuple
from config import FILE_DIR, PACKSIZE
from Server import Server
from hashlib import sha256


def signalHandler(signal, frame, socket: sk.socket):
    print("Closing socket...")
    socket.close()
    print("Quitting...")
    sys.exit(0)


def getCommandList(server: Server) -> List:
    print(f"Sending {message}")
    server.sendToServer(message)
    data, address = server.recFromServer()
    data = data.decode()
    print(data)
    commands = []
    responseList = data.split('\n')[1:-1]
    for line in responseList:
        command = line.split()
        commands.append(command[0])
    return commands


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


def checkCommandExists(inputCommand: str) -> bool:
    return inputCommand.split()[0] in commands


def checkCommandLength(inputCommand: str) -> bool:
    return len(inputCommand.split()) <= 2


def checkFileExists(inputCommand: str) -> bool:
    if inputCommand.split()[0] != "put":
        return True
    files = os.scandir(path=FILE_DIR)
    nameList = [i.name for i in files if i.is_file]
    name = inputCommand.split()[1]
    return name in nameList


def checkCommand(inputCommand: str) -> bool:
    checks = [checkCommandExists, checkCommandLength, checkFileExists]
    return False not in [check(inputCommand) for check in checks]


def getLocalSha(packList: List) -> str:
    bytesList = [i['bytes'] for i in packList]
    bytesStr = b''.join(bytesList)
    return sha256(bytesStr).hexdigest()


def recvFile(server: Server) -> Tuple:
    data, address = server.recFromServer()
    data = data.decode()
    packNum = int(data)
    packList = []
    while True:
        data, address = server.recFromServer()
        data = pickle.loads(data)
        if data['index'] == -1:
            break
        packList.append(data)
        print(f"{data['index']}/{packNum}", end='\r')
    packList.sort(key=lambda x: x['index'])
    remoteSha = data['sha']
    return packNum, packList, remoteSha


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    server_address = ('localhost', 10000)
    server = Server(sock, server_address)
    server.socket.settimeout(3.0)
    message = 'first message'
    commands = []

    # Get command list from server
    while True:
        try:
            commands = getCommandList(server)
            break
        except sk.timeout:
            print("Server timed out on first message.")
            print("Trying again...")

    signalHandler = partial(signalHandler, socket=server.socket)
    signal.signal(signal.SIGINT, signalHandler)
    print("Insert ctrl-c to quit.\n")

    while True:
        inputCommand = input("Enter command: ")
        if checkCommand(inputCommand) is False:
            print("Invalid command.")
            continue

        # Check command is valid from server
        if server.sendCommand(inputCommand) is False:
            print("Invalid command.")
            continue

        if inputCommand == "ls":
            data, address = server.recFromServer()
            data = data.decode()
            print(data)

        elif inputCommand.split()[0] == "get":
            requestedFile = inputCommand.split()[1]
            while True:
                try:
                    print(f"Starting download of {requestedFile}")
                    packNum, packList, remoteSha = recvFile(server)
                    localSha = getLocalSha(packList)
                    if localSha == remoteSha:
                        break
                    print("File hash differs, downloading again...")
                except sk.timeout:
                    # if server times out, send command again
                    server.sendCommand(inputCommand)
                    print("Server timed out, starting over.")
                    packList = []
                    continue
            with open(FILE_DIR + requestedFile, "wb") as newFile:
                for i in packList:
                    newFile.write(i['bytes'])
            print(f"Downloaded {requestedFile} file from server")

        elif inputCommand.split()[0] == "put":
            name = inputCommand.split()[1]
            try:
                packNum = getFileLen(name)
            except IOError:
                print("Error while reading file.")
                continue

            server.sendToServer(str(packNum))
            uploadList = getResponseList(name, packNum)
            for i in uploadList:
                print(f"Sending package {i['index']}/{packNum}", end="\r")
                server.sendToServer(pickle.dumps(i))
            # send end of file
            server.sendToServer(pickle.dumps({"index": -1, "bytes": b"0"}))
            try:
                data, address = server.recFromServer()
                data = data.decode()
                if data == "ACK":
                    print(f"File {name} uploaded correctly.")
                else:
                    print("Error while uploading file, try again.")
            except sk.timeout:
                print("Server timed out, file might not have been uploaded.")
        else:
            break

    print('closing socket')
    sock.close()
