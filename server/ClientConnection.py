import socket
from typing import Tuple
from config import BUFF


class ClientConnection:
    """Class that represents a server's connection with a client

    Attributes
    ----------
    sock: socket
        the socket on which the server receives and sends data
        to the client
    address: Tuple
        a Tuple containing a string representing the client's
        IP and the client's port number
    """

    def __init__(self, sock: socket.socket, address: Tuple):
        """Creates a new instance of the ClientConnection class

        Args:
            sock (socket):
                the socket on which the server receives and sends data
                to the client
            address (Tuple):
                a Tuple containing a string representing the client's
                IP and the client's port number
        """
        self.sock = sock
        self.address = address

    def send(self, toSend):
        """Sends a message to the client

        toSend: can be a string or a bytes object
        """
        if type(toSend) == str:
            toSend = toSend.encode()
        self.sock.sendto(toSend, self.address)

    def recv(self) -> Tuple:
        """Receives a message from the client

        returns a Tuple containing the reiceived data and the
        address it was received from
        """
        data, address = self.sock.recvfrom(BUFF)
        assert address == self.address
        return data, address
