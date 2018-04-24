import os
import platform
import socket

import bencode
from syncr_backend.constants import FRONTEND_UNIX_ADDRESS
from syncr_backend.init.node_init import get_full_init_directory

from .constants import BUFFER_SIZE
from .constants import TCP_ADDRESS
from .constants import TIMEOUT


def send_request(request):
    """
    Sends message to backend over socket connection and waits for a response
    :param request: dictionary of info to be sent to backend
    :return:
    """

    # Convert dictionary to send-able type
    data_string = bencode.encode(request)

    op_sys = platform.system()
    if op_sys == 'Windows':
        response_string = _tcp_send_message(data_string)
    else:
        response_string = _unix_send_message(data_string)

    response = bencode.decode(response_string)

    return response


def _tcp_send_message(msg):
    """
    Sends message to backend over tcp socket and awaits a response
    :param msg:
    :return:
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    s.connect(TCP_ADDRESS)

    # Send request
    s.sendall(msg)
    s.shutdown(socket.SHUT_WR)

    # Read response from backend
    response = b''
    while True:
        data = s.recv(BUFFER_SIZE)
        if not data:
            break
        else:
            response += data

    s.close()
    return response


def _unix_send_message(msg):
    """
    Sends message to backend over unix socket and awaits a response
    :param msg:
    :return:
    """

    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    s.connect(os.path.join(get_full_init_directory(), FRONTEND_UNIX_ADDRESS))

    # Send request
    s.sendall(msg)
    s.shutdown(socket.SHUT_WR)

    # Read response from backend
    response = b''
    while True:
        data = s.recv(BUFFER_SIZE)
        if not data:
            break
        else:
            response += data

    s.close()
    return response


if __name__ == '__main__':
    message = {
        'drop_id': 'test',
        'action': 'ACTION_SHARE_DROP',
    }
    respond = send_request(message)
    print(respond.get('status'))
