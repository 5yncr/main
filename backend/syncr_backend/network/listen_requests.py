"""The recieve side of network communication"""
import asyncio
import os
import sys
import threading
from asyncio import AbstractEventLoop
from typing import Optional  # noqa

import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import ERR_EXCEPTION
from syncr_backend.constants import ERR_NEXIST
from syncr_backend.constants import REQUEST_TYPE_CHUNK
from syncr_backend.constants import REQUEST_TYPE_CHUNK_LIST
from syncr_backend.constants import REQUEST_TYPE_DROP_METADATA
from syncr_backend.constants import REQUEST_TYPE_FILE_METADATA
from syncr_backend.constants import REQUEST_TYPE_NEW_DROP_METADATA
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import DropVersion
from syncr_backend.metadata.drop_metadata import get_drop_location
from syncr_backend.metadata.file_metadata import get_file_metadata_from_drop_id
from syncr_backend.util.fileio_util import read_chunk
from syncr_backend.util.log_util import get_logger
from syncr_backend.util.network_util import send_response


logger = get_logger(__name__)


async def request_dispatcher(
    request: dict, writer: asyncio.StreamWriter,
) -> None:
    """
    Handle and dispatch requests

    :param request: dict containing request data
    :param writer: StreamWriter to pass to the handle function
    :return: None
    """
    function_map = {
        REQUEST_TYPE_DROP_METADATA: handle_request_drop_metadata,
        REQUEST_TYPE_FILE_METADATA: handle_request_file_metadata,
        REQUEST_TYPE_CHUNK_LIST: handle_request_chunk_list,
        REQUEST_TYPE_CHUNK: handle_request_chunk,
        REQUEST_TYPE_NEW_DROP_METADATA: handle_request_new_drop_metadata,
    }
    req_type = request['request_type']
    logger.info("incomming request type: %s", req_type)
    handle_function = function_map[req_type]

    try:
        await handle_function(request, writer)
    except Exception:
        response = {
            'status': 'error',
            'error': ERR_EXCEPTION,
            'message': 'unknown error',
        }
        await send_response(writer, response)


async def async_handle_request(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
) -> None:
    """Handle a request by reading the data and passing it to dispatcher

    :param reader: StreamReader
    :param writer: StreamWriter
    """
    request = b''
    while 1:
        data = await reader.read()
        if not data:
            break
        else:
            request += data
        logger.info('Data received')
    await request_dispatcher(bencode.decode(request), writer)


async def handle_request_drop_metadata(
    request: dict, writer: asyncio.StreamWriter,
) -> None:
    """
    Handle a drop metadata request

    :param request: \
    { \
    "protocol_version": int, \
    "request_type": DROP_METADATA (int), \
    "drop_id": string, \
    "version": string (optional), \
    "nonce": string (optional) \
    }
    :param writer: StreamWriter
    :return: None
    """
    file_location = await get_drop_location(request['drop_id'])
    file_location = os.path.join(file_location, DEFAULT_DROP_METADATA_LOCATION)
    if request.get('version') is not None and request.get('nonce') is not None:
        drop_version = DropVersion(
            int(request['version']), int(request['nonce']),
        )  # type: Optional[DropVersion]
    else:
        drop_version = None
    request_drop_metadata = await DropMetadata.read_file(
        id=request['drop_id'],
        metadata_location=file_location,
        version=drop_version,
    )

    if request_drop_metadata is None:
        logger.info("drop metadata not found, sending error")
        response = {
            'status': 'error',
            'error': ERR_NEXIST,
        }
    else:
        logger.info("sending drop metadata")
        response = {
            'status': 'ok',
            'response': await request_drop_metadata.encode(),
        }

    await send_response(writer, response)


async def handle_request_file_metadata(
    request: dict, writer: asyncio.StreamWriter,
) -> None:
    """
    Handles a request for a file metadata

    :param request: \
    { \
    "protocol_version": int, \
    "request_type": FILE_METADATA (int), \
    "file_id": string, \
    'drop_id": string \
    }
    :param writer: StreamWriter
    :return: None
    """
    request_file_metadata = await get_file_metadata_from_drop_id(
        request['drop_id'],
        request['file_id'],
    )

    if request_file_metadata is None:
        logger.info("file metadata not found, sending error")
        response = {
            'status': 'error',
            'error': ERR_NEXIST,
        }
    else:
        logger.info("sending file metadata")
        response = {
            'status': 'ok',
            'response': request_file_metadata.encode(),
        }

    await send_response(writer, response)


async def handle_request_chunk_list(
    request: dict, writer: asyncio.StreamWriter,
) -> None:
    """
    Handles a request for a file chunk list avaiable on this node

    :param request: \
    { \
    "protocol_version": int, \
    "request_type": CHUNK_LIST (int), \
    'drop_id": string, \
    "file_id": string \
    }
    :param writer: StreamWriter
    :return: None
    """
    request_file_metadata = await get_file_metadata_from_drop_id(
        request['drop_id'],
        request['file_id'],
    )

    if request_file_metadata is None:
        logger.info("file metadata not found, sending error")
        response = {
            'status': 'error',
            'error': ERR_NEXIST,
        }
    else:
        chunks = await request_file_metadata.downloaded_chunks
        logger.info("sending chunk list")
        response = {
            'status': 'ok',
            'response': list(chunks),
        }

    await send_response(writer, response)


async def handle_request_chunk(
    request: dict, writer: asyncio.StreamWriter,
) -> None:
    """
    Handles a request for a chunk that is avaliable on this chunk

    :param request: \
    { \
    "protocol_version": int, \
    "request_type": CHUNK (int), \
    "file_id": string, \
    'drop_id": string \
    "index": string, \
    }
    :param writer: StreamWriter
    :return: None
    """
    request_file_metadata = await get_file_metadata_from_drop_id(
        request['drop_id'],
        request['file_id'],
    )
    drop_location = await get_drop_location(request['drop_id'])
    drop_metadata_location = os.path.join(
        drop_location, DEFAULT_DROP_METADATA_LOCATION,
    )
    request_drop_metadata = await DropMetadata.read_file(
        id=request['drop_id'], metadata_location=drop_metadata_location,
    )

    if request_file_metadata is None or request_drop_metadata is None:
        logger.info("chunk not found")
        response = {
            'status': 'error',
            'error': ERR_NEXIST,
        }
    else:
        file_name = request_drop_metadata.get_file_name_from_id(
            request['file_id'],
        )
        chunk = (await read_chunk(
            os.path.join(
                drop_location, file_name,
            ), request['index'],
        ))[0]
        logger.info("sending chunk")
        logger.debug("chunk len: %s", len(chunk))
        response = {
            'status': 'ok',
            'response': chunk,
        }

    await send_response(writer, response)


async def handle_request_new_drop_metadata(
    request: dict, writer: asyncio.StreamWriter,
) -> None:
    """
    :param request: \
    { \
    "protocol_version": int, \
    "request_type": NEW_DROP_METADATA (int), \
    "latest_version_id": int, \
    "latest_version_nonce": int \
    }
    :param writer: StreamWriter
    :return: None
    """
    logger.warning("tried and failed to accept a new_drop_metadata request")
    pass


async def start_listen_server(
    tcp_ip: str,
    tcp_port: str,
) -> asyncio.events.AbstractServer:
    """
    Start the listen server

    :param tcp_ip: Address to bind to
    :param tcp_port: Port to bind to
    :return: An asyncio Server
    """
    return await asyncio.start_server(
        async_handle_request, tcp_ip, int(tcp_port),
    )


def listen_requests(
    tcp_ip: str,
    tcp_port: str,
    loop: AbstractEventLoop,
    shutdown_flag: threading.Event,
) -> None:
    """Run the request server until closing"""
    coro = asyncio.start_server(
        async_handle_request, tcp_ip, int(tcp_port), loop=loop,
    )
    server = loop.run_until_complete(coro)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == '__main__':
    listen_requests(
        sys.argv[1], sys.argv[0], asyncio.get_event_loop(), threading.Event(),
    )
