from math import ceil
import signal
import socket as sk
import os
import sys

PACKSIZE = 8192
FILE_DIR = "./files/"

class Server:
    def __init__(self, socket, server_address):
        self.socket = socket
        self.address = server_address

    def recFromServer(self):
        received, address = self.socket.recvfrom(PACKSIZE)
        return received.decode(), address

    def sendToServer(self, message):
        return self.socket.sendto(message.encode(), self.address)

def signalHandler(signal, frame):
    print("\nExiting...\n")
    sys.exit(0)

if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    server_address = ('localhost', 10000)
    server = Server(sock, server_address)
    server.socket.settimeout(3)
    message = 'first message'
    commands = []

    # Get command list from server
    while True:
        try:
            print (f'sending "{message}"')
            sent = server.sendToServer(message)
    
            print('waiting for server response\n')
            received, address = server.recFromServer()
            print(received)
    
            # Create available commands list
            responseList = received.split('\n')[1:-1]
            for word in responseList:
                command = word.split()
                commands.append(command[0])
            break
        except Exception as info:
            continue
        
    signal.signal(signal.SIGINT, signalHandler)
    print("Insert ctrl-c to quit.\n")

    while True:
        inputCommand = input("Ender command: ")
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
            print(nameList)
            name = inputCommand.split()[1]
            if name not in nameList:
                print(f"File {name} not found.")
                currDir = os.getcwd()
                print(f"Make sure the file is in the {currDir}/files directory.")
                continue

        # Check command is valid from server
        sent = server.sendToServer(inputCommand)
        data, address = server.recFromServer()
        if data == "ACK":
            print("Valid command")
        elif data == "Invalid command":
            print("Invalid command")
            continue
            
        
        if inputCommand == "ls":
            data, address = server.recFromServer()
            print(data)
        elif inputCommand.split()[0] == "get":
            requestedFile = inputCommand.split()[1]
            print(f"Starting download of {requestedFile}")
            with open(FILE_DIR + requestedFile, "w") as newFile:
                data, address = server.recFromServer()
                packNum = int(data)
                for i in range(packNum):
                    data, address = server.recFromServer()
                assert i == int(data)
                server.sendToServer(str(i))
                data, address = server.recFromServer()
                newFile.write(data)
                print(f"Received package number {i}/{packNum}", end="\r")

            print(f"Downloaded {requestedFile} file from server")
        elif inputCommand.split()[0] == "put":
            try: 
                name = FILE_DIR + inputCommand.split()[1]
                with open(name, "r") as toUpload:
                    data = toUpload.read()
                packNum = 1
                dataSize = len(data.encode())
                if dataSize > PACKSIZE:
                    packNum = ceil(dataSize / PACKSIZE)
            except:
                exit() # TODO
            server.sendToServer(str(packNum))
            with open(name, "r") as toUpload:
                uploadList = []
                for i in range(packNum):
                    uploadList.append(toUpload.read(PACKSIZE))
            for i in range(packNum):
                print(f"Sending package number {i}/{packNum}", end="\r")
                server.sendToServer(str(i))
                data, address = server.recFromServer()
                assert i == int(data)
                server.sendToServer(uploadList[i])
            print(f"File {name} uploaded correctly.")
        else:
            break

    print ('closing socket')
    sock.close()
    