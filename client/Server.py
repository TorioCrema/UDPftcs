from config import BUFF
import socket
from typing import Tuple


class Server:
    def __init__(self, socket: socket.socket, server_address):
        self.socket = socket
        self.address = server_address

    def recFromServer(self) -> Tuple:
        received, address = self.socket.recvfrom(BUFF)
        return received, address

    def sendToServer(self, message: bytes):
        if type(message) == str:
            message = message.encode()
        return self.socket.sendto(message, self.address)

    def sendCommand(self, command: str) -> bool:
        self.sendToServer(command)
        data, address = self.recFromServer()
        data = data.decode()
        return data == "ACK"
