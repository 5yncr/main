"""The send side of network communications"""
import asyncio
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar

import bencode  # type: ignore

from syncr_backend.constants import PROTOCOL_VERSION
from syncr_backend.constants import REQUEST_TYPE_CHUNK
from syncr_backend.constants import REQUEST_TYPE_CHUNK_LIST
from syncr_backend.constants import REQUEST_TYPE_DROP_METADATA
from syncr_backend.constants import REQUEST_TYPE_FILE_METADATA
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import DropVersion
from syncr_backend.metadata.file_metadata import FileMetadata
from syncr_backend.util import network_util
from syncr_backend.util.log_util import get_logger
from syncr_backend.util.network_util import raise_network_error


R = TypeVar('R')

logger = get_logger(__name__)


async def do_request(
    request_fun: Callable[..., Awaitable[R]],
    peers: List[Tuple[str, int]],
    fun_args: Dict[str, Any],
) -> R:
    """Helper function for sending a request to many peers.  Will try calling
    request_fun with fun_args for peers in peers until one succeeds

    :param request_fun: The request function.  Must take an ip, port, and \
    some number of kwargs
    :param peers: A list of peers to try to talk to
    :param fun_args: The arguments to pass to request_fun for each peer
    :raises network_util.NoPeersException: If no peers are provided
    :return: The result of a successful call to request_fun
    """
    result = None
    last_err = Exception("This shouldn't happen")
    if not peers:
        logger.error("no peers provided to do_request")
        raise network_util.NoPeersException("no peers provided to do_request")

    for (ip, port) in peers:
        try:
            result = await request_fun(ip, port, **fun_args)
        except (TimeoutError, network_util.SyncrNetworkException) as e:
            last_err = e
            pass
        else:
            break

    if result is None:
        logger.error("no good results from peers")
        raise last_err

    return result


async def send_drop_metadata_request(
    ip: str,
    port: int,
    drop_id: bytes,
    drop_version: Optional[DropVersion]=None,
    protocol_version: Optional[int]=PROTOCOL_VERSION,
) -> DropMetadata:
    """
    Sends drop metadata request to node at ip and port

    :param ip: ip address of node
    :param port: port of the node
    :param drop_id: drop_id of the requested drop
    :param protocol_version: protocol_version of the request
    :param drop_version: version of the drop
    :return: DropMetadata object
    """
    request_dict = {
        'protocol_version': protocol_version,
        'request_type': REQUEST_TYPE_DROP_METADATA,
        'drop_id': drop_id,
    }
    if drop_version is not None:
        request_dict['version'] = drop_version.version
        request_dict['nonce'] = drop_version.nonce

    drop_metadata_bytes = await send_request_to_node(
        request_dict,
        ip,
        port,
    )
    logger.debug("recieved drop metadata")
    return await DropMetadata.decode(drop_metadata_bytes)


async def send_file_metadata_request(
    ip: str,
    port: int,
    drop_id: bytes,
    file_id: bytes,
    protocol_version: Optional[int]=PROTOCOL_VERSION,
) -> FileMetadata:
    """
    Sends file metadata request to node at ip and port

    :param ip: ip address of node
    :param port: port of the node
    :param drop_id: the drop id
    :param file_id: file_id of the requested file
    :param protocol_version: protocol_version of the request
    :return: FileMetadata object
    """
    request_dict = {
        'protocol_version': protocol_version,
        'request_type': REQUEST_TYPE_FILE_METADATA,
        'file_id': file_id,
        'drop_id': drop_id,
    }

    file_metadata_bytes = await send_request_to_node(
        request_dict,
        ip,
        port,
    )
    logger.debug("recieved file metadata")
    return FileMetadata.decode(file_metadata_bytes)


async def send_chunk_list_request(
    ip: str,
    port: int,
    drop_id: bytes,
    file_id: bytes,
    protocol_version: Optional[int]=PROTOCOL_VERSION,
) -> List[int]:
    """
    Sends chunk list request to node at ip and port

    :param ip: ip address of node
    :param port: port of the node
    :param drop_id: the drop id
    :param file_id: file_id of the requested chunk list
    :param protocol_version: protocol_version of the request
    :return: List[int] of indexes of the file
    """
    request_dict = {
        'protocol_version': protocol_version,
        'request_type': REQUEST_TYPE_CHUNK_LIST,
        'file_id': file_id,
        'drop_id': drop_id,
    }

    chunk_index_list = await send_request_to_node(
        request_dict,
        ip,
        port,
    )
    logger.debug("recieved chunk list")
    return chunk_index_list


async def send_chunk_request(
    ip: str,
    port: int,
    drop_id: bytes,
    file_id: bytes,
    file_index: int,
    protocol_version: Optional[int]=PROTOCOL_VERSION,
) -> bytes:
    """
    Sends chunk request to node at ip and port

    :param ip: ip address of node
    :param port: port of the node
    :param drop_id: the drop id
    :param file_id: file_id of the requested chunk
    :param file_index: index of the file for the chunk
    :param protocol_version: protocol_version of the request
    :return: bytes of the actual chunk
    """
    request_dict = {
        'protocol_version': protocol_version,
        'request_type': REQUEST_TYPE_CHUNK,
        'file_id': file_id,
        'drop_id': drop_id,
        'index': file_index,
    }

    chunk = await send_request_to_node(
        request_dict,
        ip,
        port,
    )
    logger.debug("recieved chunk")
    if type(chunk) == str:
        return chunk.encode('utf-8')
    else:
        return chunk


async def send_request_to_node(
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
    reader, writer = await asyncio.open_connection(ip, port)

    writer.write(bencode.encode(request))
    writer.write_eof()
    await writer.drain()

    data = b''
    while 1:
        sockdata = await reader.read()
        if not sockdata:
            break
        data += sockdata
    reader.feed_eof()

    response = bencode.decode(data)
    if (response['status'] == 'ok'):
        logger.debug("sending OK")
        return response['response']
    else:
        logger.debug("sending error")
        raise_network_error(response['error'])
