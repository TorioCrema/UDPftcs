from functools import partial
import pickle
import signal
import socket as sk
import os
from config import FILE_DIR, BUFF, PACKSIZE, COMMANDS, TIMEOUT_TIMER
from math import ceil
import sys
from typing import List, Tuple
from ClientConnection import ClientConnection
from time import sleep
from hashlib import sha256


def intSignalHandler(signal, frame, socket: sk.socket):
    """Handler for interrupt signal from standard input

    Args:
        socket (socket): the socket that will be colsed before
        quitting the execution
    """
    print("\nClosing socket.")
    socket.close()
    print("Quitting...")
    sys.exit(0)


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


def recvFile(clientConn: ClientConnection) -> Tuple:
    """Receives from clientConn until end of file

    Can throw a timeout exception

    Args:
        clientConn (ClientConnection): the ClientConnection object
        from which to receive the data

    Returns:
        Tuple: a tuple with the number of packs the file was split into,
        the list of received data and the correct hash of the file
    """
    clientConn.sock.settimeout(TIMEOUT_TIMER)
    data, address = clientConn.recv()
    data = data.decode()
    packNum = int(data)
    if packNum == -1:
        return packNum, [], ""
    packList = []
    while True:
        data, address = clientConn.recv()
        data = pickle.loads(data)
        if data['index'] == -1:
            break
        packList.append(data)
        print(f"Receiving packet {data['index']}/{packNum}")
    packList.sort(key=lambda x: x['index'])
    return packNum, packList, data['sha']


def writeFile(fileName: str, packList: List):
    """Writes into a new file the bytes for a list

    Args:
        fileName (str): the name of the file to write into
        packList (List): the list of dictionaries containig
        the bytes of the file
    """
    with open(FILE_DIR + fileName, "wb") as file:
        for pack in packList:
            file.write(pack['bytes'])


if __name__ == "__main__":
    sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    intSignalHandler = partial(intSignalHandler, socket=sock)
    signal.signal(signal.SIGINT, intSignalHandler)

    server_address = ('localhost', 10000)
    print(f'Starting up on {server_address[0]} port {server_address[1]}')
    sock.bind(server_address)

    while True:
        try:
            sock.settimeout(None)
            print('waiting to receive message...')
            data, address = sock.recvfrom(BUFF)
            clientConn = ClientConnection(sock, address)
            dataLen = len(data)
            print(f'received {dataLen} bytes from {address}')
            command = data.decode('utf8')
            print(command)

            if command == 'ls':
                # Sends valid command ACK to the client
                clientConn.send("ACK")
                # Gets all files in the default file directry
                files = os.scandir(path=FILE_DIR)
                response = 'Available files:\n'
                for entry in files:
                    if entry.is_file:
                        response += entry.name + "\n"
                clientConn.send(response.encode())
            elif command.split()[0] == "get":
                name = command.split()[1]
                try:
                    packNum = getFileLen(name)
                except IOError:
                    clientConn.send("Invalid command")
                    continue
                # Sends valid command ACK to the client
                clientConn.send("ACK")
                clientConn.send(str(packNum))

                responseList = getResponseList(name, packNum)
                for i in responseList:
                    print(f"Sending package {i['index']}/{packNum}", end='\r')
                    clientConn.send(pickle.dumps(i))
                    # sleeps so as not to fill the clients buffer
                    sleep(0.0001)
                # send file hash
                localHash = getLocalSha(responseList)
                clientConn.send(pickle.dumps({"index": -1, "sha": localHash}))

            elif command.split()[0] == "put":
                # Sends valid command ACK to the client
                clientConn.send("ACK")
                requestedFile = command.split()[1]
                print(f"Starting download of {requestedFile}")
                try:
                    packNum, packList, remoteSha = recvFile(clientConn)
                    if getLocalSha(packList) != remoteSha:
                        print("Error while downloading file")
                        print("Aborting operation.")
                        clientConn.send("Error")
                    else:
                        writeFile(requestedFile, packList)
                        print(f"{requestedFile} downloaded from client")
                        clientConn.send("ACK")
                except sk.timeout or IOError:
                    print("Error while downloading file, aborting operation.")
                    clientConn.send("Error")
            else:
                clientConn.send(COMMANDS)
        except (AssertionError, UnicodeDecodeError):
            print("A different client has made a request")
            print("Resetting server state.")
            continue
