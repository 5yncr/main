from typing import List
from typing import Optional

from syncr_backend.constants import PROTOCOL_VERSION
from syncr_backend.constants import REQUEST_TYPE_CHUNK
from syncr_backend.constants import REQUEST_TYPE_CHUNK_LIST
from syncr_backend.constants import REQUEST_TYPE_DROP_METADATA
from syncr_backend.constants import REQUEST_TYPE_FILE_METADATA
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import DropVersion
from syncr_backend.metadata.file_metadata import FileMetadata
from syncr_backend.util import network_util


def send_drop_metadata_request(
    ip: str,
    port: int,
    drop_id: str,
    protocol_version: Optional[int]=PROTOCOL_VERSION,
    drop_version: Optional[DropVersion]=None,
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
    file_id: str,
    protocol_version: Optional[int]=PROTOCOL_VERSION,
) -> FileMetadata:
    """
    Sends file metadata request to node at ip and port
    :param ip: ip address of node
    :param port: port of the node
    :param file_id: file_id of the requested file
    :param protocol_version: protocol_version of the request
    :return: FileMetadata object
    """
    request_dict = {
        'protocol_version': protocol_version,
        'request_type': REQUEST_TYPE_FILE_METADATA,
        'file_id': file_id,
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
    file_id: str,
    protocol_version: Optional[int]=PROTOCOL_VERSION,
) -> List[int]:
    """
    Sends chunk list request to node at ip and port
    :param ip: ip address of node
    :param port: port of the node
    :param file_id: file_id of the requested chunk list
    :param protocol_version: protocol_version of the request
    :return: List[int] of indexes of the file
    """
    request_dict = {
        'protocol_version': protocol_version,
        'request_type': REQUEST_TYPE_CHUNK_LIST,
        'file_id': file_id,
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
    file_id: str,
    file_index: int,
    protocol_version: Optional[int]=PROTOCOL_VERSION,
) -> bytes:
    """
    Sends chunk request to node at ip and port
    :param ip: ip address of node
    :param port: port of the node
    :param file_id: file_id of the requested chunk
    :param file_index: index of the file for the chunk
    :param protocol_version: protocol_version of the request
    :return: bytes of the actual chunk
    """
    request_dict = {
        'protocol_version': protocol_version,
        'request_type': REQUEST_TYPE_CHUNK,
        'file_id': file_id,
        'index': file_index,
    }

    chunk = network_util.send_request_to_node(
        request_dict,
        ip,
        port,
    )
    return chunk
