from config import BUFF
import socket
from typing import Tuple


class Server:
    """Class that represents the server

    Attributes
    ----------
    socket: socket
        the socket on which the client receives ands sends data
        to the client
    address: Tuple
        a Tuple containing a string representing the server's
        IP and it's port number
    """
    def __init__(self, socket: socket.socket, server_address):
        """Creates a new instance of the class

        Args:
            socket (socket): the socket on which the client receives
            and sends data to the server
            address (Tuple): a Tuple containing a string representing
        """
        self.socket = socket
        self.address = server_address

    def recFromServer(self) -> Tuple:
        """Receieves a message from the client

        Returns:
            Tuple: a Tuple containig the data received and
            the address it was received from
        """
        received, address = self.socket.recvfrom(BUFF)
        return received, address

    def sendToServer(self, message) -> int:
        """Sends a packet to the server

        Args:
            message: the data to send to the server
        """
        if type(message) == str:
            message = message.encode()
        return self.socket.sendto(message, self.address)

    def sendCommand(self, command: str) -> bool:
        """Sends a command to the server and checks that
        the command is valid

        Args:
            command (str): the command to send to the server

        Returns:
            bool: True if the command is valid, False otherwise
        """
        self.sendToServer(command)
        data, address = self.recFromServer()
        data = data.decode()
        return data == "ACK"
