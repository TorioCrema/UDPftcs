from functools import partial
import pickle
from math import ceil
import signal
import socket as sk
import os
import sys
from time import sleep
from typing import List, Tuple
from config import FILE_DIR, PACKSIZE, TIMEOUT_TIMER, SERVER_ADDRESS
from Server import Server
from hashlib import sha256


def signalHandler(signal, frame, socket: sk.socket):
    """Handler for interrupt signal from standard input

    Args:
        socket (socket): the socket that will be closed before
        quitting the execution
    """
    print("\nClosing socket...")
    socket.close()
    print("Quitting...")
    sys.exit(0)


def getCommandList(server: Server) -> List:
    """Receives and parses the available commands from the server

    Args:
        sever (Server): the server from which to receive the list
        of commands

    Returns:
        List: the list of available commands as strings
    """
    message = "first message"
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
    """Returns the number of packets a file will be sent in

    Args:
        fileName (str): the name of the file from which the
        packet number will be calculated
    """
    fileName = FILE_DIR + fileName
    with open(fileName, "rb") as file:
        response = file.read()
    packNum = 1
    responseSize = len(response)
    if responseSize > PACKSIZE:
        packNum = ceil(responseSize / PACKSIZE)
    return packNum


def getResponseList(fileName: str, segmentNumber: int) -> List:
    """Returns the list of packets to send to the client

    Args:
        fileName (str): the name of the file to send to the client
        segmentNumber (int) the number of segments the file will be
        split into

    Returns:
        List: a list of dictionaries with index and bytes keys
    """
    with open(FILE_DIR + fileName, "rb") as file:
        responseList = []
        for i in range(segmentNumber):
            toSend = {"index": i, "bytes": file.read(PACKSIZE)}
            responseList.append(toSend)
    return responseList


def checkCommandExists(inputCommand: str) -> bool:
    """Checks if a command is in the available commands list"""
    return inputCommand.split()[0] in commands


def checkCommandLength(inputCommand: str) -> bool:
    """Checks that a command has no more that 2 strings in it"""
    return len(inputCommand.split()) <= 2


def checkFileExists(inputCommand: str) -> bool:
    """Checks that the file for a 'put' command exists"""
    if inputCommand.split()[0] != "put":
        return True
    files = os.scandir(path=FILE_DIR)
    nameList = [i.name for i in files if i.is_file]
    name = inputCommand.split()[1]
    return name in nameList


def checkCommand(inputCommand: str) -> bool:
    """Executes all checks on a command"""
    checks = [checkCommandExists, checkCommandLength, checkFileExists]
    return False not in [check(inputCommand) for check in checks]


def getLocalSha(packList: List) -> str:
    """Returns the sha256 of the received packList

    Args:
        packList (List): the list of dictionaries received from the client

    Returns:
        str: the hex encoded string representing the sha256 hash of the
        concatenated bytes list
    """
    bytesList = [i['bytes'] for i in packList]
    bytesStr = b''.join(bytesList)
    return sha256(bytesStr).hexdigest()


def recvFile(server: Server) -> Tuple:
    """Receives from Server unti end of file

    Can throw a timeout exeption

    Args:
        server (Server): the Server from which to receive
        the data

    Returns:
        Tuple: a tuple with the number of packs the file war
        split into the list of received data and the correct
        hash of the file
    """
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
    return packNum, packList, data['sha']


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    server_address = SERVER_ADDRESS
    server = Server(sock, server_address)
    server.socket.settimeout(TIMEOUT_TIMER)
    commands = []
    signalHandler = partial(signalHandler, socket=server.socket)
    signal.signal(signal.SIGINT, signalHandler)
    print("Insert ctrl-c to quit.")

    # Get command list from server
    while True:
        try:
            commands = getCommandList(server)
            break
        except sk.timeout:
            print("Server timed out on first message.")
            print("Trying again...")

    while True:
        inputCommand = input("Enter command: ")
        if checkCommand(inputCommand) is False:
            print("Invalid command.")
            continue

        # Check command is valid from server
        try:
            if server.sendCommand(inputCommand) is False:
                print("Invalid command.")
                continue
        except sk.timeout:
            print("Server timedout, trying again...")
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
                    server.sendToServer(inputCommand)
                    print("Server timed out, starting over.")
                    packList = []
                    continue
            with open(FILE_DIR + requestedFile, "wb") as newFile:
                for i in packList:
                    newFile.write(i['bytes'])
            print(f"Downloaded {requestedFile} file from server")

        elif inputCommand.split()[0] == "put":
            name = inputCommand.split()[1]
            while True:
                try:
                    packNum = getFileLen(name)
                except IOError:
                    print("Error while reading file.")
                    server.sendToServer(str(-1))
                    break

                server.sendToServer(str(packNum))
                uploadList = getResponseList(name, packNum)
                for i in uploadList:
                    print(f"Sending package {i['index']}/{packNum}", end="\r")
                    server.sendToServer(pickle.dumps(i))
                    sleep(0.0001)
                # send file hash
                localHash = getLocalSha(uploadList)
                hashPack = {"index": -1, "sha": localHash}
                server.sendToServer(pickle.dumps(hashPack))
                try:
                    data, address = server.recFromServer()
                    data = data.decode()
                    if data == "ACK":
                        print(f"File {name} uploaded correctly.")
                        break
                    else:
                        print("Error while uploading file, trying again.")
                        server.sendToServer(inputCommand)
                except sk.timeout:
                    print("Server timed out trying again.")
                    server.sendToServer(inputCommand)
        else:
            break

    print('closing socket')
    sock.close()
