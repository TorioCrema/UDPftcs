import socket
from typing import Tuple
from config import BUFF


class ClientConnection:
    def __init__(self, sock: socket.socket, address):
        self.sock = sock
        self.address = address

    def send(self, toSend):
        if type(toSend) == str:
            toSend = toSend.encode()
        self.sock.sendto(toSend, self.address)

    def recv(self) -> Tuple:
        data, address = self.sock.recvfrom(BUFF)
        return data, address
