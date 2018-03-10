import socket
from socket import SHUT_WR
from typing import Any
from typing import Dict

import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_BUFFER_SIZE
from syncr_backend.constants import ERR_INCOMPAT
from syncr_backend.constants import ERR_NEXIST


class NotExistException(Exception):
    """Requested object does not exist"""
    pass


class IncompatibleProtocolVersionException(Exception):
    """Version number of the protocol not compatible with request"""
    pass


def raise_network_error(
    errno: int,
) -> None:
    """Raises an error based on the errno"""
    exceptionmap = {
        ERR_NEXIST: NotExistException,
        ERR_INCOMPAT: IncompatibleProtocolVersionException,
    }
    raise exceptionmap[errno]


def send_request_to_node(
    request: Dict[str, Any], ip: str, port: int,
) -> Any:
    """
    Creates a connection a node and sends a given request to the
    node and returns the response
    :param port: port where node is serving
    :param ip: ip of node
    :param request: Dictionary of a request as specified in the Spec Document
    :return: node response
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        s.send(bencode.encode(request))
        s.shutdown(SHUT_WR)
        data = b''
        while 1:
            sockdata = s.recv(DEFAULT_BUFFER_SIZE)
            if not sockdata:
                break
            data += sockdata
        s.close()

        response = bencode.decode(data)
        if (response['status'] == 'ok'):
            return response['response']
        else:
            raise_network_error(response['error'])

    except socket.timeout:
        s.close()
        raise TimeoutError('ERROR: backend connection socket timed out')
