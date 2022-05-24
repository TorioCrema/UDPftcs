from functools import partial
import pickle
from math import ceil
import signal
import socket as sk
import os
import sys
from typing import List
from config import FILE_DIR, PACKSIZE
from Server import Server


def signalHandler(signal, frame, socket: sk.socket):
    socket.close()
    print("\nExiting...\n")
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


def checkCommandExists(inputCommand: str) -> bool:
    return inputCommand.split()[0] in commands


def checkCommandLength(inputCommand: str) -> bool:
    return len(inputCommand.split()[0]) > 2


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
            print("Command invalid")
            break

        # Check command is valid from server
        if server.sendCommand(inputCommand) is False:
            print("Invalid command.")
            break

        if inputCommand == "ls":
            data, address = server.recFromServer()
            data = data.decode()
            print(data)

        elif inputCommand.split()[0] == "get":
            requestedFile = inputCommand.split()[1]
            packNum = -1
            packList = []
            while len(packList) != packNum:
                try:
                    print(f"Starting download of {requestedFile}", end='\r')
                    data, address = server.recFromServer()
                    data = data.decode()
                    packNum = int(data)
                    data, address = server.recFromServer()
                    data = pickle.loads(data)
                    while data['index'] != -1:
                        packList.insert(data["index"], data["bytes"])
                        data, address = server.recFromServer()
                        data = pickle.loads(data)
                except sk.timeout:
                    # if server times out, send command again
                    server.sendCommand(inputCommand)
                    print("Server timed out, starting over.")
                    packList = []
                    continue
            with open(FILE_DIR + requestedFile, "wb") as newFile:
                for i in packList:
                    newFile.write(i)
            print(f"Downloaded {requestedFile} file from server")

        elif inputCommand.split()[0] == "put":
            try:
                name = FILE_DIR + inputCommand.split()[1]
                with open(name, "rb") as toUpload:
                    data = toUpload.read()
                packNum = 1
                dataSize = len(data)
                if dataSize > PACKSIZE:
                    packNum = ceil(dataSize / PACKSIZE)
            except IOError:
                print("Error while reading file.")
                continue
            server.sendToServer(str(packNum))
            with open(name, "rb") as toUpload:
                uploadList = []
                for i in range(packNum):
                    uploadList.append(
                        {"index": i, "bytes": toUpload.read(PACKSIZE)}
                    )
            for i in range(packNum):
                print(f"Sending package number {i}/{packNum}", end="\r")
                server.sendToServer(pickle.dumps(uploadList[i]))
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
