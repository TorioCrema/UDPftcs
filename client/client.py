import pickle
from math import ceil
import signal
import socket as sk
import os
import sys
from typing import Tuple

PACKSIZE = 8192
BUFF = 16384
FILE_DIR = "./files/"

class Server:
    def __init__(self, socket: sk.socket, server_address):
        self.socket = socket
        self.address = server_address

    def recFromServer(self) -> Tuple:
        received, address = self.socket.recvfrom(BUFF)
        return received, address

    def sendToServer(self, message: bytes):
        return self.socket.sendto(message, self.address)

    def sendStrToServer(self, message: str):
        return self.sendToServer(message.encode())

def signalHandler(signal, frame):
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
            print (f'sending "{message}"')
            sent = server.sendStrToServer(message)
    
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
            files = os.scandir(path = FILE_DIR)
            nameList = [i.name for i in files if i.is_file]
            name = inputCommand.split()[1]
            if name not in nameList:
                print(f"File {name} not found.")
                currDir = os.getcwd()
                print(f"Make sure the file is in the {currDir}/files directory.")
                continue

        # Check command is valid from server
        sent = server.sendStrToServer(inputCommand)
        data, address = server.recFromServer()
        data = data.decode()
        if data == "ACK":
            print("Valid command")
        else:
            print("Invalid command")
            continue
            
        
        if inputCommand == "ls":
            data, address = server.recFromServer()
            data = data.decode()
            print(data)
        elif inputCommand.split()[0] == "get":
            requestedFile = inputCommand.split()[1]
            print(f"Starting download of {requestedFile}")
            data, address = server.recFromServer()
            data = data.decode()
            packNum = int(data)
            packList = []
            missingList = [i for i in range(packNum)]
            # receive until end of transmission from server or timeout
            try:
                data, address = server.recFromServer()
                data = pickle.loads(data)
                while data['index'] != -1:
                    packList.insert(data["index"], data["bytes"])
                    missingList.remove(data["index"])
                    data, address = server.recFromServer()
                    data = pickle.loads(data)
            except sk.timeout:
                print("Server timedout during file transmission")

            # request each missing pack individually
            current = 0
            while current < len(missingList):
                try:
                    server.sendStrToServer(str(missingList[current]))
                    data, address = server.recFromServer()
                    data = pickle.loads(data)
                    if data["index"] != missingList[current]:
                        continue
                    packList.insert(data["index"], data["bytes"])
                    current += 1
                except sk.timeout:
                    pass

            server.sendStrToServer("-1")

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
            except:
                exit() # TODO
            server.sendStrToServer(str(packNum))
            with open(name, "rb") as toUpload:
                uploadList = []
                for i in range(packNum):
                    uploadList.append(toUpload.read(PACKSIZE))
            for i in range(packNum):
                print(f"Sending package number {i}/{packNum}", end="\r")
                server.sendStrToServer(str(i))
                data, address = server.recFromServer()
                data = data.decode()
                assert i == int(data)
                server.sendToServer(uploadList[i])
            print(f"File {name} uploaded correctly.")
        else:
            break

    print ('closing socket')
    sock.close()
    