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

def sendCommand(command: str, server: Server) -> bool:
    sent = server.sendStrToServer(command)
    data, address = server.recFromServer()
    data = data.decode()
    return data == "ACK"

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
                currDir = os.getcwd()
                print(f"File {name} not found.\nMake sure the file is in the {currDir}/files directory.")
                continue

        # Check command is valid from server
        if sendCommand(inputCommand, server) == False:
            print("Invalid command.")
            break
            
        
        if inputCommand == "ls":
            data, address = server.recFromServer()
            data = data.decode()
            print(data)

        elif inputCommand.split()[0] == "get":
            packNum = -1
            packList = []
            while len(packList) != packNum:
                try:
                    requestedFile = inputCommand.split()[1]
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
                    sendCommand(inputCommand, server)
                    print("Server timed out, starting over.")
                    packList = []
                    continue
                
            # request each missing pack individually

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
    

