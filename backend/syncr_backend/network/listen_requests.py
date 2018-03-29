"""The recieve side of network communication"""
import os
import socket
import sys
import threading
from socket import SHUT_RD
from typing import Optional  # noqa

import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_BUFFER_SIZE
from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import ERR_NEXIST
from syncr_backend.constants import REQUEST_TYPE_CHUNK
from syncr_backend.constants import REQUEST_TYPE_CHUNK_LIST
from syncr_backend.constants import REQUEST_TYPE_DROP_METADATA
from syncr_backend.constants import REQUEST_TYPE_FILE_METADATA
from syncr_backend.constants import REQUEST_TYPE_NEW_DROP_METADATA
from syncr_backend.metadata import drop_metadata
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import DropVersion
from syncr_backend.metadata.drop_metadata import get_drop_location
from syncr_backend.metadata.file_metadata import get_file_metadata_from_drop_id
from syncr_backend.util.fileio_util import read_chunk
from syncr_backend.util.network_util import send_response


def request_dispatcher(request: dict, conn: socket.socket) -> None:
    """

    :param request: dict containing request data
    :param conn: socket.accept() connection
    :return: None
    """
    function_map = {
        REQUEST_TYPE_DROP_METADATA: handle_request_drop_metadata,
        REQUEST_TYPE_FILE_METADATA: handle_request_file_metadata,
        REQUEST_TYPE_CHUNK_LIST: handle_request_chunk_list,
        REQUEST_TYPE_CHUNK: handle_request_chunk,
        REQUEST_TYPE_NEW_DROP_METADATA: handle_request_new_drop_metadata,
    }
    type = request['request_type']
    handle_function = function_map[type]

    handle_function(request, conn)


def handle_request_drop_metadata(request: dict, conn: socket.socket) -> None:
    """

    :param request:
    {
    "protocol_version": int,
    "request_type": DROP_METADATA (int),
    "drop_id": string,
    "version": string (optional),
    "nonce": string (optional)
    }
    :param conn: socket.accept() connection
    :return: None
    """
    file_location = get_drop_location(request['drop_id'])
    if request.get('version') is not None and request.get('nonce') is not None:
        drop_version = DropVersion(
            int(request['version']), int(request['nonce']),
        )  # type: Optional[DropVersion]
    else:
        drop_version = None
    request_drop_metadata = DropMetadata.read_file(
        request['drop_id'],
        os.path.join(file_location, DEFAULT_DROP_METADATA_LOCATION),
        drop_version,
    )

    if request_drop_metadata is None:
        response = {
            'status': 'error',
            'error': ERR_NEXIST,
        }
    else:
        response = {
            'status': 'ok',
            'response': request_drop_metadata.encode(),
        }

    send_response(conn, response)


def handle_request_file_metadata(request: dict, conn: socket.socket) -> None:
    """
    Handles a request for a file metadata
    :param request:
    {
    "protocol_version": int,
    "request_type": FILE_METADATA (int),
    "file_id": string
    'drop_id": string
    }
    :param conn: socket.accept() connection
    :return: None
    """
    request_file_metadata = get_file_metadata_from_drop_id(
        request['drop_id'],
        request['file_id'],
    )

    if request_file_metadata is None:
        response = {
            'status': 'error',
            'error': ERR_NEXIST,
        }
    else:
        response = {
            'status': 'ok',
            'response': request_file_metadata.encode(),
        }

    send_response(conn, response)


def handle_request_chunk_list(request: dict, conn: socket.socket) -> None:
    """
    Handles a request for a file chunk list avaiable on this node
    :param request:
    {
    "protocol_version": int,
    "request_type": CHUNK_LIST (int),
    'drop_id": string
    "file_id": string
    }
    :param conn: socket.accept() connection
    :return: None
    """
    request_file_metadata = get_file_metadata_from_drop_id(
        request['drop_id'],
        request['file_id'],
    )

    if request_file_metadata is None:
        response = {
            'status': 'error',
            'error': ERR_NEXIST,
        }
    else:
        chunks = request_file_metadata.downloaded_chunks
        response = {
            'status': 'ok',
            'response': list(chunks),
        }

    send_response(conn, response)


def handle_request_chunk(request: dict, conn: socket.socket) -> None:
    """
    Handles a request for a chunk that is avaliable on this chunk
    :param request:
    {
    "protocol_version": int,
    "request_type": CHUNK (int),
    "file_id": string,
    'drop_id": string
    "index": string,
    }
    :param conn: socket.accept() connection
    :return: None
    """
    request_file_metadata = get_file_metadata_from_drop_id(
        request['drop_id'],
        request['file_id'],
    )
    drop_location = drop_metadata.get_drop_location(request['drop_id'])
    drop_metadata_location = os.path.join(
        drop_location, DEFAULT_DROP_METADATA_LOCATION,
    )
    request_drop_metadata = DropMetadata.read_file(
        request['drop_id'], drop_metadata_location,
    )

    if request_file_metadata is None or request_drop_metadata is None:
        response = {
            'status': 'error',
            'error': ERR_NEXIST,
        }
    else:
        file_name = request_drop_metadata.get_file_name_from_id(
            request['file_id'],
        )
        chunk = read_chunk(
            os.path.join(
                drop_location, file_name,
            ), request['index'],
        )
        response = {
            'status': 'ok',
            'response': chunk,
        }

    send_response(conn, response)


def handle_request_new_drop_metadata(
    request: dict, conn: socket.socket,
) -> None:
    """
    :param request:
    {
    "protocol_version": int,
    "request_type": NEW_DROP_METADATA (int),
    "latest_version_id": int,
    "latest_version_nonce": int
    }
    :param conn: socket.accept() connection
    :return: None
    """
    pass


def listen_requests(
    tcp_ip: str,
    tcp_port: str,
    shutdown_flag: threading.Event,
) -> None:
    """
    runs the main tcp requests loop
    :param tcp_ip: ip to bind to
    :param tcp_port: port to bind to
    :param shutdown_flag: flag to be set to shutdown the thread
    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((tcp_ip, int(tcp_port)))
    s.listen(5)

    while not shutdown_flag.is_set():
        conn, addr = s.accept()
        print(type(conn))
        print('Connection address:', addr)
        request = b''
        while 1:
            data = conn.recv(DEFAULT_BUFFER_SIZE)
            if not data:
                break
            else:
                request += data
            print('Data received')
        s.shutdown(SHUT_RD)
        request_dispatcher(bencode.decode(request), conn)
        s.close()


if __name__ == '__main__':
    listen_requests(sys.argv[1], sys.argv[0], threading.Event())
