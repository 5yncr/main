"""Helper functions for sending tracker requests"""
import asyncio
from typing import Any
from typing import Dict

import bencode  # type: ignore

from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


async def send_request_to_tracker(
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
    reader, writer = await asyncio.open_connection(ip, port)

    writer.write(bencode.encode(request))
    writer.write_eof()
    await writer.drain()

    response = b''
    while 1:
        data = await reader.read()
        if not data:
            break
        else:
            response += data

    reader.feed_eof()

    return bencode.decode(response)
