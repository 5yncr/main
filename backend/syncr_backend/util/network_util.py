"""Helper functions for communicating with other peers"""
import socket
from socket import SHUT_WR
from typing import Any
from typing import Dict

import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_BUFFER_SIZE
from syncr_backend.constants import ERR_INCOMPAT
from syncr_backend.constants import ERR_NEXIST
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


def send_response(conn: socket.socket, response: Dict[Any, Any]) -> None:
    """
    Sends a response to a connection and then closes writing to that connection
    :param conn: socket.accept() connection
    :param response: Dict[Any, Any] response
    :return: None
    """
    conn.send(bencode.encode(response))
    conn.shutdown(SHUT_WR)


class SyncrNetworkException(Exception):
    """Base exception for network errors"""
    pass


class NotExistException(SyncrNetworkException):
    """Requested object does not exist"""
    pass


class IncompatibleProtocolVersionException(SyncrNetworkException):
    """Version number of the protocol not compatible with request"""
    pass


class NoPeersException(SyncrNetworkException):
    """No peers found or provided to a request function"""
    pass


def raise_network_error(
    errno: int,
) -> None:
    """Raises an error based on the errno"""
    logger.debug("Raising exception %s", errno)
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
            logger.debug("sending OK")
            return response['response']
        else:
            logger.debug("sending error")
            raise_network_error(response['error'])

    except socket.timeout:
        s.close()
        raise TimeoutError('ERROR: backend connection socket timed out')
