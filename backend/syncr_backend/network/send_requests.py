from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import TypeVar

from syncr_backend.constants import PROTOCOL_VERSION
from syncr_backend.constants import REQUEST_TYPE_CHUNK
from syncr_backend.constants import REQUEST_TYPE_CHUNK_LIST
from syncr_backend.constants import REQUEST_TYPE_DROP_METADATA
from syncr_backend.constants import REQUEST_TYPE_FILE_METADATA
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import DropVersion
from syncr_backend.metadata.file_metadata import FileMetadata
from syncr_backend.util import network_util


R = TypeVar('R')


def do_request(
    request_fun: Callable[..., R],
    peers: List[Tuple[str, int]],
    fun_args: Dict[str, Any],
) -> R:
    result = None
    last_err = Exception("This shouldn't happen")

    for (ip, port) in peers:
        try:
            result = request_fun(ip, port, **fun_args)
        except (TimeoutError, network_util.SyncrNetworkException) as e:
            last_err = e
            pass
        else:
            break

    if result is None:
        raise last_err

    return result


def send_drop_metadata_request(
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

    drop_metadata_bytes = network_util.send_request_to_node(
        request_dict,
        ip,
        port,
    )
    return DropMetadata.decode(drop_metadata_bytes)


def send_file_metadata_request(
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

    file_metadata_bytes = network_util.send_request_to_node(
        request_dict,
        ip,
        port,
    )
    return FileMetadata.decode(file_metadata_bytes)


def send_chunk_list_request(
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

    chunk_index_list = network_util.send_request_to_node(
        request_dict,
        ip,
        port,
    )
    return chunk_index_list


def send_chunk_request(
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

    chunk = network_util.send_request_to_node(
        request_dict,
        ip,
        port,
    )
    return chunk
