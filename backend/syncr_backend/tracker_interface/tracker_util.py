"""Helper functions for sending tracker requests"""
import socket
from socket import SHUT_RD
from socket import SHUT_WR
from typing import Any
from typing import Dict

import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_BUFFER_SIZE


def send_request_to_tracker(
    request: Dict[str, Any], ip: str, port: int,
) -> Dict[str, Any]:
    """
    Creates a connection with the tracker and sends a given request to the
    tracker and returns the response
    :param port: port where tracker is serving
    :param ip: ip of tracker
    :param request: ['POST'/'GET', node_id|drop_id, data]
    :return: tracker response
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        s.send(bencode.encode(request))
        s.shutdown(SHUT_WR)

        response = b''
        while 1:
            data = s.recv(DEFAULT_BUFFER_SIZE)
            if not data:
                break
            else:
                response += data
        s.shutdown(SHUT_RD)
        s.close()

        return bencode.decode(response)
    except socket.timeout:
        s.close()
        raise TimeoutError('ERROR: Tracker server timeout')
