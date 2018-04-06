import socket
from typing import Any
from typing import Dict

from syncr_backend.constants import ACTION_ACCEPT_CHANGES
from syncr_backend.constants import ACTION_ACCEPT_CONFLICT_FILE
from syncr_backend.constants import ACTION_ADD_FILE
from syncr_backend.constants import ACTION_ADD_OWNER
from syncr_backend.constants import ACTION_DECLINE_CHANGES
from syncr_backend.constants import ACTION_DECLINE_CONFLICT_FILE
from syncr_backend.constants import ACTION_DELETE_DROP
from syncr_backend.constants import ACTION_GET_CONFLICTING_FILES
from syncr_backend.constants import ACTION_GET_OWNED_DROPS
from syncr_backend.constants import ACTION_GET_SELECT_DROPS
from syncr_backend.constants import ACTION_GET_SUB_DROPS
from syncr_backend.constants import ACTION_INPUT_DROP_TO_SUBSCRIBE_TO
from syncr_backend.constants import ACTION_INPUT_NAME
from syncr_backend.constants import ACTION_REMOVE_FILE
from syncr_backend.constants import ACTION_REMOVE_OWNER
from syncr_backend.constants import ACTION_REQUEST_CHANGE
from syncr_backend.constants import ACTION_SHARE_DROP
from syncr_backend.constants import ACTION_TRANSFER_OWNERSHIP
from syncr_backend.constants import ACTION_UNSUBSCRIBE
from syncr_backend.constants import ACTION_VIEW_CONFLICTS
from syncr_backend.constants import ACTION_VIEW_PENDING_CHANGES
from syncr_backend.constants import ERR_INVINPUT
from syncr_backend.util.network_util import send_response


def handle_frontend_request(
        request: Dict[str, Any], conn: socket.socket,
) -> None:

    function_map = {
        ACTION_ACCEPT_CHANGES: handle_accept_changes,
        ACTION_ACCEPT_CONFLICT_FILE: handle_accept_conflict_file,
        ACTION_ADD_FILE: handle_add_file,
        ACTION_ADD_OWNER: handle_add_owner,
        ACTION_DECLINE_CHANGES: handle_decline_changes,
        ACTION_DECLINE_CONFLICT_FILE: handle_decline_conflict_file,
        ACTION_DELETE_DROP: handle_delete_drop,
        ACTION_GET_CONFLICTING_FILES: handle_get_conflicting_files,
        ACTION_GET_OWNED_DROPS: handle_get_owned_drops,
        ACTION_GET_SELECT_DROPS: handle_get_selected_drops,
        ACTION_GET_SUB_DROPS: handle_get_subscribed_drops,
        ACTION_INPUT_DROP_TO_SUBSCRIBE_TO: handle_input_subscribe_drop,
        ACTION_INPUT_NAME: handle_input_name,
        ACTION_REMOVE_FILE: handle_remove_file,
        ACTION_REMOVE_OWNER: handle_remove_owner,
        ACTION_REQUEST_CHANGE: handle_request_change,
        ACTION_SHARE_DROP: handle_share_drop,
        ACTION_TRANSFER_OWNERSHIP: handle_transfer_ownership,
        ACTION_UNSUBSCRIBE: handle_unsubscribe,
        ACTION_VIEW_CONFLICTS: handle_view_conflicts,
        ACTION_VIEW_PENDING_CHANGES: handle_view_pending_changes,
    }

    action = request['action']
    handle_function = function_map.get(action)

    if handle_function is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
        send_response(conn, response)
    else:
        handle_function(request, conn)


def handle_accept_changes(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to accept changes in a file.
    :param request:
    {
    "action": string
    "drop_id": string
    "file_path": string
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
        # TODO: backend logic to apply changes to current file.
        # TODO: Test if given drop_ids and file_paths are valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'changes accepted',
        }

    send_response(conn, response)


def handle_transfer_ownership(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to transfer ownership from one drop to
    another.
    :param request:
    {
    'action': string
    'transfer_owner_id' : string
    }
    :param conn: socket.accept() connection
    :return: None
    """

    if request['transfer_owner_id'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        # TODO: backend logic to apply ownership transfer.
        new_owner = request['transfer_owner_id']
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'Primary Ownership transferred to ' + new_owner,
        }

    send_response(conn, response)


def handle_accept_conflict_file(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to accept a file that is in conflict with another.
    :param request:
    {
    "action": string
    "drop_id": string
    "file_path": string
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
        # TODO: backend logic to accept a conflict file and decline others.
        # TODO: Test if given drop_id and file_path are valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'file accepted',
        }

    send_response(conn, response)


def handle_add_file(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to add a file to a drop.
    :param request:
    {
    "action": string
    "drop_id": string
    "file_path": string
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
        # TODO: backend logic to add file to drop.
        # TODO: Test if given drop_id and file_path are valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'file added to drop',
        }

    send_response(conn, response)


def handle_add_owner(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to an owner to a drop
    :param request:
    {
    "action": string
    "drop_id": string
    "owner_id": string
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
        # TODO: backend logic to add owner to owner list.
        # TODO: Test if given drop_id and owner_id are valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'owner successfully added',
        }

    send_response(conn, response)


def handle_decline_changes(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to decline changes in a file.
    :param request:
    {
    "action": string
    "drop_id": string
    "file_path": string
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
        # TODO: backend logic to decline a change - leaving drop unchanged
        # TODO: Test if given drop_id and file_path are valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'changes declined',
        }

    send_response(conn, response)


def handle_decline_conflict_file(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to decline a file that is in conflict with another.
    :param request:
    {
    "action": string
    "drop_id": string
    "file_path": string
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
        # TODO: backend logic to decline a file in conflict with others
        # TODO: Test if given drop_id and file_path are valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'conflicting file declined',
        }

    send_response(conn, response)


def handle_delete_drop(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to delete a drop.
    :param request:
    {
    "action": string
    "drop_id": string
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
        # TODO: backend logic to delete a drop
        # TODO: Test if given drop_id is valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'drop successfully deleted',
        }

    send_response(conn, response)


def handle_get_conflicting_files(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to view files in drop that conflict each other.
    :param request:
    {
    "action": string
    "drop_id": string
    "file_path": string
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
        # TODO: backend logic to retrieve list of conflicting files.
        # TODO: Test if given drop_id and file_path are valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'conflicting files retrieved',
        }

    send_response(conn, response)


def handle_get_owned_drops(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to retrieve drops owned by individual.
    :param request:
    {
    "action": string
    }
    :param conn: socket.accept() connection
    :return: None
    """

    # TODO: backend logic to retrieve owned drops.
    response = {
        'status': 'ok',
        'result': 'success',
        'message': 'owned drops retrieved',
    }

    send_response(conn, response)


def handle_get_selected_drops(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to a drop selected by user.
    :param request:
    {
    "action": string
    "drop_id": string
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
        # TODO: backend logic to retrieve info on selected drop.
        # TODO: Test if given drop_id is valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'selected files retrieved',
        }

    send_response(conn, response)


def handle_get_subscribed_drops(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to retrieve drops that user is subscribed to.
    :param request:
    {
    "action": string
    }
    :param conn: socket.accept() connection
    :return: None
    """

    # TODO: backend logic to retrieve subscribed drops.
    response = {
        'status': 'ok',
        'result': 'success',
        'message': 'subscribed drops retrieved',
    }

    send_response(conn, response)


def handle_input_subscribe_drop(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to subscribe to drop that user specifies.
    :param request:
    {
    "action": string
    "drop_name": string
    }
    :param conn: socket.accept() connection
    :return: None
    """
    if request['drop_name'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        # TODO: backend logic to subscribe to drop.
        # TODO: Test if given drop_name is valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'subscribed to drop ' + request['drop_name'],
        }

    send_response(conn, response)


def handle_input_name(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to create drop whose name is specified by user.
    :param request:
    {
    "action": string
    "drop_name": string
    }
    :param conn: socket.accept() connection
    :return: None
    """
    if request['drop_name'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        # TODO: backend logic to create a drop.
        # TODO: Test if given drop_name is valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'Drop ' + request['drop_name'] + ' created',
        }

    send_response(conn, response)


def handle_remove_file(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to remove file from drop.
    :param request:
    {
    "action": string
    "drop_id": string
    "file_name": string
    }
    :param conn: socket.accept() connection
    :return: None
    """
    if request['drop_id'] is None or request['file_name'] is None:
        response = {
            'status': 'error',
            'error': ERR_INVINPUT,
        }
    else:
        # TODO: backend logic to remove file from drop.
        # TODO: Test if given drop_id and file_name are valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'file successfully removed',
        }

    send_response(conn, response)


def handle_remove_owner(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to remove an owner from a drop
    :param request:
    {
    "action": string
    "drop_id": string
    "owner_id": string
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
        # TODO: Backend logic to remove owner.
        # TODO: Handle if drop_id or owner_id is not valid.
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'owner successfully removed',
        }

    send_response(conn, response)


def handle_request_change(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to request a change in the drop.
    :param request:
    {
    "action": string
    "drop_id": string
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
        # TODO: Add given changes to list of requested changes.
        # TODO: Handle if given drop_id is not valid
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'pending changes submitted',
        }

    send_response(conn, response)


def handle_share_drop(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to retrieve id that can be shared with other nodes.
    :param request:
    {
    "action": string
    "drop_id": string
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

    send_response(conn, response)


def handle_unsubscribe(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to unsubscribe from a subscribed drop.
    :param request:
    {
    "action": string
    "drop_id": string
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
        # TODO: Backend logic to unsubscribe from drop.
        # TODO: Handle if given drop_id is not valid
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'unsubscribed from drop ' + request['drop_id'],
        }

    send_response(conn, response)


def handle_view_conflicts(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to view conflicting files in drop.
    :param request:
    {
    "action": string
    "drop_id": string
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
        # TODO: Backend logic to retrieve conflicting files in drop.
        # TODO: Handle if given drop_id is not valid
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'conflicting files retrieved',
        }

    send_response(conn, response)


def handle_view_pending_changes(
        request: Dict[str, Any], conn: socket.socket,
) -> None:
    """
    Handling function to view pending changes in the drop.
    :param request:
    {
    "action": string
    "drop_id": string
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
        # TODO: Backend logic to retrieve pending changes of drop.
        # TODO: Handle if given drop_id is not valid
        response = {
            'status': 'ok',
            'result': 'success',
            'message': 'pending changes retrieved',
        }

    send_response(conn, response)
