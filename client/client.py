from distutils.command.upload import upload
from math import ceil
import socket as sk
import time
import os

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


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    server_address = ('localhost', 10000)
    server = Server(sock, server_address)
    message = 'first message'
    commands = []

    # Get command list from server
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

    except Exception as info:
        print(info)
        exit
        
    print("Insert ctrl-c to quit.")

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
            nameList = [i for i in files if i.is_file]
            name = inputCommand.split()[1]
            if name not in nameList:
                print(f"File {name} not found.")
                currDir = os.getcwd()
                print(f"Make sure the file is in the {currDir}/files directory.")
                continue

        # Check command is valid from server
        commandReceived = False
        while commandReceived == False:
            sent = server.sendToServer(inputCommand)
            data, address = server.recFromServer()
            print(f"data={data}")
            if data == "ACK":
                print("Valid command")
                commandReceived = True
            elif data == "Invalid command":
                print("Invalid command")
                break
            
        
        if inputCommand == "ls":
            data, address = server.recFromServer()
            print(data)
        elif inputCommand.split()[0] == "get":
            requestedFile = inputCommand.split()[1]
            print(f"Starting download of {requestedFile}")
            with open(requestedFile, "w") as newFile:
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
                name = inputCommand.split()[1]
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


        else:
            break

    print ('closing socket')
    sock.close()
    