import asyncio
import os
import platform
from typing import Any
from typing import Awaitable  # noqa
from typing import Callable  # noqa
from typing import Dict

import bencode  # type: ignore

from syncr_backend.constants import ACTION_ADD_OWNER
from syncr_backend.constants import ACTION_DELETE_DROP
from syncr_backend.constants import ACTION_GET_OWNED_SUBSCRIBED_DROPS
from syncr_backend.constants import ACTION_GET_SELECT_DROPS
from syncr_backend.constants import ACTION_INITIALIZE_DROP
from syncr_backend.constants import ACTION_INPUT_DROP_TO_SUBSCRIBE_TO
from syncr_backend.constants import ACTION_REMOVE_OWNER
from syncr_backend.constants import ACTION_SHARE_DROP
from syncr_backend.constants import ACTION_UNSUBSCRIBE
from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import ERR_EXCEPTION
from syncr_backend.constants import ERR_INVINPUT
from syncr_backend.constants import FRONTEND_TCP_ADDRESS
from syncr_backend.constants import FRONTEND_UNIX_ADDRESS
from syncr_backend.init.drop_init import initialize_drop
from syncr_backend.init.node_init import get_full_init_directory
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import get_drop_location
from syncr_backend.util import crypto_util
from syncr_backend.util.drop_util import check_for_changes
from syncr_backend.util.drop_util import get_drop_metadata
from syncr_backend.util.drop_util import get_file_names_percent
from syncr_backend.util.drop_util import get_owned_subscribed_drops_metadata
from syncr_backend.util.drop_util import sync_drop
from syncr_backend.util.drop_util import update_drop
from syncr_backend.util.log_util import get_logger
from syncr_backend.util.network_util import send_response


logger = get_logger(__name__)


async def handle_frontend_request(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handle a request from the frontend

    :param request: The request dict
    :param conn: The StreamWriter to write the response to
    """
    function_map = {
        ACTION_ADD_OWNER: handle_add_owner,
        ACTION_DELETE_DROP: handle_delete_drop,
        ACTION_GET_OWNED_SUBSCRIBED_DROPS: handle_get_owned_subscribed_drops,
        ACTION_GET_SELECT_DROPS: handle_get_selected_drops,
        ACTION_INPUT_DROP_TO_SUBSCRIBE_TO: handle_input_subscribe_drop,
        ACTION_INITIALIZE_DROP: handle_initialize_drop,
        ACTION_REMOVE_OWNER: handle_remove_owner,
        ACTION_SHARE_DROP: handle_share_drop,
        ACTION_UNSUBSCRIBE: handle_unsubscribe,
    }  # type: Dict[str, Callable[[Dict[str, Any], asyncio.StreamWriter], Awaitable[None]]]  # noqa

    action = request['action']
    handle_function = function_map.get(action)

    if handle_function is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
        await send_response(conn, response)
    else:
        try:
            await handle_function(request, conn)
        except Exception as e:
            response = {
                'status': 'error',
                'error': ERR_EXCEPTION,
                'message': str(e),
            }
            await send_response(conn, response)


async def handle_add_owner(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to an owner to a drop

    :param request: { \
    "action": string, \
    "drop_id": string, \
    "owner_id": string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """
    if request['drop_id'] is None or request['owner_id'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'owner successfully added',
        }
        drop_id = crypto_util.b64decode(request['drop_id'])
        owner_id = crypto_util.b64decode(request['owner_id'])

        update_drop(
            drop_id,
            add_secondary_owner=owner_id,
        )

        md = await get_drop_metadata(drop_id, [])

        if owner_id not in md.other_owners:
            response['result'] = 'failure'
            response['message'] = 'unable to add owner to drop'

    await send_response(conn, response)


async def handle_delete_drop(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to delete a drop.

    :param request: { \
    "action": string, \
    "drop_id": string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """
    if request['drop_id'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        drop_id = crypto_util.b64decode(request['drop_id'])
        file_location = await get_drop_location(drop_id)
        file_location = os.path.join(
            file_location,
            DEFAULT_DROP_METADATA_LOCATION,
        )
        drop_metadata = await DropMetadata.read_file(
            id=drop_id,
            metadata_location=file_location,
        )
        if drop_metadata is None:
            response = {
                'status': 'error',
                'error': ERR_INVINPUT,
            }
        else:
            await drop_metadata.delete()
            response = {
                'status': 'ok',
                'result': 'success',
                'message': 'drop successfully deleted',
            }

    await send_response(conn, response)


async def handle_get_selected_drops(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to a drop selected by user.

    :param request: { \
    "action": string, \
    "drop_id": string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """

    if request['drop_id'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        drop_id = crypto_util.b64decode(request['drop_id'])
        md = await get_drop_metadata(drop_id, [])
        drop = drop_metadata_to_response(md)
        file_update_status = await check_for_changes(request['drop_id'])
        if file_update_status is None or drop is None:
            response = {
                'status': 'error',
                'result': 'failure',
                'requested_drops': {},
                'message': 'drop retrieval failed',
            }
        else:
            response = {
                'status': 'ok',
                'result': 'success',
                'message': 'selected files retrieved',
                'requested_drops': drop,
                'pending_changes': {
                    'added': file_update_status.added,
                    'removed': file_update_status.removed,
                    'changed': file_update_status.changed,
                    'unchanged': file_update_status.unchanged,
                },
            }

    await send_response(conn, response)


async def handle_get_owned_subscribed_drops(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to retrieve drops that user owns and is subscribed to

    :param request: { \
    'action': string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """

    md_tup = await get_owned_subscribed_drops_metadata()

    owned_drop_dictionaries = []
    subscribed_drop_dictionaries = []

    owned_drops = md_tup[0]
    subscribed_drops = md_tup[1]

    for drop in owned_drops:
        owned_drop_dictionaries.append(drop_metadata_to_response(drop))

    for drop in subscribed_drops:
        subscribed_drop_dictionaries.append(drop_metadata_to_response(drop))

    dict_tup = (owned_drop_dictionaries, subscribed_drop_dictionaries)

    response = {
        'status': 'ok',
        'result': 'success',
        'requested_drops_tuple': dict_tup,
        'message': 'owned and subscribed drops retrieved.',
    }

    await send_response(conn, response)


async def handle_input_subscribe_drop(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to subscribe to drop that user specifies.

    :param request: { \
    "action": string, \
    "drop_id": string, \
    "file_path": string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """
    if request['drop_id'] is None or request['file_path'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:

        drop_id = request['drop_id']
        file_path = request['file_path']

        try:
            asyncio.ensure_future(sync_drop(drop_id, file_path))
            response = {
                'status': 'ok',
                'result': 'success',
                'message': 'subscribed to drop ' + request['drop_id'],
            }
        except RuntimeError:
            response = {
                'status': 'error',
                'result': 'failure',
                'message': 'Cannot subscribe to drop!',
            }

    await send_response(conn, response)


async def handle_initialize_drop(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to create drop whose name is specified by user.

    :param request: { \
    "action": string, \
    "drop_name": string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """
    # This code assumes that the user has already
    # created a folder to initialize as a drop.
    #
    # First, we check to see if tracker already contains drop id
    # If so, do nothing, send message failure back
    #
    # Else, initialize directory with 'drop_name' as the name of the drop

    # TODO: Allow user to select directory location from UI (on frontend).

    directory = request['directory']
    drop_name = os.path.basename(directory)

    status = 'error'
    result = 'failure'

    # TODO: Change 'False' to check if drop id already exists in tracker
    if False:
        message = 'A drop already exists with the given drop name'
    else:

        try:
            await initialize_drop(directory)
        except RuntimeError:
            message = 'Error in initializing drop.'
        else:
            status = 'ok'
            result = 'success'
            message = 'Drop ' + drop_name + 'created'

    response = {
        'status': status,
        'result': result,
        'message': message,
    }

    await send_response(conn, response)


async def handle_remove_owner(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to remove an owner from a drop

    :param request: { \
    "action": string, \
    "drop_id": string, \
    "owner_id": string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """

    if request['drop_id'] is None or request['owner_id'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        drop_id = crypto_util.b64decode(request['drop_id'])
        owner_id = crypto_util.b64decode(request['owner_id'])
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'owner successfully removed',
        }

        await update_drop(
            drop_id,
            remove_secondary_owner=owner_id,
        )

        md = await get_drop_metadata(drop_id, [])

        if owner_id in md.other_owners:
            response['result'] = 'failure'
            response['message'] = 'unable to remove owner from drop'

    await send_response(conn, response)


async def handle_share_drop(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to retrieve id that can be shared with other nodes.

    :param request: { \
    "action": string, \
    "drop_id": string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """
    if request['drop_id'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        # TODO: Backend logic to get drop info to share to others.
        # TODO: Handle if given drop_id is not valid
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'drop information retrieved',
        }

    await send_response(conn, response)


async def handle_unsubscribe(
        request: Dict[str, Any], conn: asyncio.StreamWriter,
) -> None:
    """
    Handling function to unsubscribe from a subscribed drop.

    :param request: { \
    "action": string, \
    "drop_id": string, \
    }
    :param conn: socket.accept() connection
    :return: None
    """
    if request['drop_id'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        drop_id = crypto_util.b64decode(request['drop_id'])
        file_location = await get_drop_location(drop_id)
        file_location = os.path.join(
            file_location, DEFAULT_DROP_METADATA_LOCATION,
        )
        drop_metadata = await DropMetadata.read_file(
            id=drop_id,
            metadata_location=file_location,
        )
        if drop_metadata is None:
            response = {
                'status': 'error',
                'error': ERR_INVINPUT,
            }
        else:
            await drop_metadata.unsubscribe()
            response = {
                'status': 'ok',
                'result': 'success',
                'message': 'unsubscribed from drop ' + request['drop_id'],
            }

    await send_response(conn, response)


# Helper functions for structure of responses
async def drop_metadata_to_response(md: DropMetadata) -> Dict[str, Any]:
    """
    Converts dropMetadata object into frontend readable dictionary.

    :param md: DropMetadata object
    :return: Dictionary for frontend
    """
    files = await get_file_names_percent(md.id)
    response = {
        'drop_id': crypto_util.b64encode(md.id),
        'name': md.name,
        'version': "%s" % md.version,
        'previous_versions': ["%s" % v for v in md.previous_versions],
        'primary_owner': crypto_util.b64encode(md.owner),
        'other_owners': [crypto_util.b64encode(o) for o in md.other_owners],
        'signed_by': crypto_util.b64encode(md.signed_by),
        'files': {n: int(p*100) for n, p in files.items()},
    }

    return response


# Functions for handling incoming frontend requests
async def setup_frontend_server() -> asyncio.events.AbstractServer:
    """
    Listens for request from frontend and then sends response

    :return: An asyncio Server, either Unix socket or TCP socket
    """

    op_sys = platform.system()
    if op_sys == 'Windows':
        return await _tcp_handle_request()
    else:
        return await _unix_handle_request()


async def async_handle_request(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter,
) -> None:
    """
    Handle an async request.  Reads from reader, then call function
    dispatcher

    :param reader: The StreamReader to read from
    :param writer: The StreamWriter the response will go to
    """
    request = b''

    while 1:
        data = await reader.read()
        if not data:
            break
        else:
            request += data
    await handle_frontend_request(bencode.decode(request), writer)


async def _tcp_handle_request() -> asyncio.events.AbstractServer:
    """
    Listens for request from frontend and sends response over tcp socket

    :return: An asyncio Server for TCP requests
    """

    return await asyncio.start_server(
        async_handle_request,
        host=FRONTEND_TCP_ADDRESS[0],
        port=FRONTEND_TCP_ADDRESS[1],
    )


async def _unix_handle_request() -> asyncio.events.AbstractServer:
    """
    Listens for request from frontend and sends response over unix socket

    :return: An asyncio Server for Unix sockets
    """

    try:
        os.unlink(
            os.path.join(get_full_init_directory(), FRONTEND_UNIX_ADDRESS),
        )
    except OSError:
        # does not yet exist, do nothing
        pass

    return await asyncio.start_unix_server(
        async_handle_request, path=os.path.join(
            get_full_init_directory(), FRONTEND_UNIX_ADDRESS,
        ),
    )


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(setup_frontend_server())
    asyncio.get_event_loop().run_forever()
