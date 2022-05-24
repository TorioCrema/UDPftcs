from functools import partial
import pickle
from math import ceil
import signal
import socket as sk
import os
import sys
from config import FILE_DIR, PACKSIZE
from Server import Server


def signalHandler(signal, frame, socket: sk.socket):
    socket.close()
    print("\nExiting...\n")
    sys.exit(0)


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
            print(f'sending "{message}"')
            sent = server.sendToServer(message)
            print('waiting for server response\n')
            received, address = server.recFromServer()
            received = received.decode()
            print(received)
            # Create available commands list
            responseList = received.split('\n')[1:-1]
            for word in responseList:
                command = word.split()
                commands.append(command[0])
            break
        except Exception as info:
            print(info)
            continue

    signalHandler = partial(signalHandler, socket=server.socket)
    signal.signal(signal.SIGINT, signalHandler)
    print("Insert ctrl-c to quit.\n")

    while True:
        inputCommand = input("Enter command: ")
        # Check that command is in command list from server
        if inputCommand.split()[0] not in commands:
            print("Please insert a valid command.")
            continue

        # Check number of files in command
        if len(inputCommand.split()) > 2:
            print("Please upload or download one file at a time.")
            continue

        # Check that upload file exists
        if inputCommand.split()[0] == "put":
            files = os.scandir(path=FILE_DIR)
            nameList = [i.name for i in files if i.is_file]
            name = inputCommand.split()[1]
            if name not in nameList:
                currDir = os.getcwd()
                print(f"File {name} not found.")
                print("Make sure the file is in the ", end="")
                print(f"{currDir}/files directory.")
                continue

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
