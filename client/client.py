import socket as sk
import time
from typing_extensions import dataclass_transform

def recFromServer(socket):
    received, server = socket.recvfrom(4096)
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
        data, server = sock.recvfrom(4096)
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

    while True:
        inputCommand = input("Ender command: ")
        sent = sock.sendto(inputCommand.encode(), server_address)

        if inputCommand == "ls":
            data = recFromServer(sock)
            print(data)
        elif "get" in inputCommand:
            # TODO
            print("not implemented")
        else:
            break

    print ('closing socket')
    sock.close()
    


