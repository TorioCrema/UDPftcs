import socket as sk
import time

PACKSIZE = 4096

def recFromServer(socket):
    received, server = socket.recvfrom(PACKSIZE)
    data = received.decode('utf8')
    return data


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    server_address = ('localhost', 10000)
    message = 'first message'
    commands = []

    # Get command list from server
    try:
        print (f'sending "{message}"')
        sent = sock.sendto(message.encode(), server_address)

        print('waiting for server response\n')
        data, server = sock.recvfrom(PACKSIZE)
        received = data.decode('utf8')
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
            sent = sock.sendto(inputCommand.encode(), server_address)
            data = recFromServer(sock)
            if data == "ACK":
                print("Valid command")
                commandReceived = True
                sock.sendto("ACK".encode(), server_address)
            elif data == "Invalid command":
                print("Invalid command")
                break
            
        

        if inputCommand == "ls":
            data = recFromServer(sock)
            print(data)
        elif "get" in inputCommand:
            requestedFile = inputCommand.split()[1]
            print(f"Starting download of {requestedFile}")
            with open(requestedFile, "w") as newFile:
                packNum = int(recFromServer(sock))
                for i in range(packNum):
                    newFile.write(recFromServer(sock))
                    print(f"Received package number {i}...")
            print(f"Downloaded {requestedFile} file from server")
        else:
            break

    print ('closing socket')
    sock.close()
    