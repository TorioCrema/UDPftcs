import socket as sk
import time

PACKSIZE = 8192

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
        if inputCommand.split()[0] not in commands:
            print("Please insert a valid command.")
            continue
        
        commandReceived = False
        while commandReceived == False:
            sent = server.sendToServer(inputCommand)
            data, address = server.recFromServer()
            if data == "ACK":
                print("Valid command")
                commandReceived = True
                #server.sendToServer("ACK")
            elif data == "Invalid command":
                print("Invalid command")
                break
            
        

        if inputCommand == "ls":
            data, address = server.recFromServer()
            print(data)
        elif "get" in inputCommand:
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
        else:
            break

    print ('closing socket')
    sock.close()
    