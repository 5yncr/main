"""
import asyncio
from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import Mock

from syncr_backend.constants import ACTION_ADD_FILE
from syncr_backend.constants import ACTION_ADD_OWNER
from syncr_backend.constants import ACTION_DELETE_DROP
from syncr_backend.constants import ACTION_GET_OWNED_DROPS
from syncr_backend.constants import ACTION_GET_SELECT_DROPS
from syncr_backend.constants import ACTION_GET_SUB_DROPS
from syncr_backend.constants import ACTION_INITIALIZE_DROP
from syncr_backend.constants import ACTION_INPUT_DROP_TO_SUBSCRIBE_TO
from syncr_backend.constants import ACTION_REMOVE_FILE
from syncr_backend.constants import ACTION_REMOVE_OWNER
from syncr_backend.constants import ACTION_SHARE_DROP
from syncr_backend.constants import ACTION_TRANSFER_OWNERSHIP
from syncr_backend.constants import ACTION_UNSUBSCRIBE
# from syncr_backend.network.handle_frontend import handle_frontend_request


# Bear in mind, the only functions that are going to be tested are the
# ones with full backend functionality by the time the final commit is due.
# Some functions have been left intentionally untested until they
# have been fully implemented.


def test_handle_frontend_request() -> None:

    from syncr_backend.network.handle_frontend import handle_frontend_request

    conn = Mock()
    conn.send = MagicMock()

    with mock.patch(
        'syncr_backend.network.handle_frontend.handle_add_file',
        autospec=True,
    ) as mock_handle_add_file, mock.patch(
        'syncr_backend.network.handle_frontend.handle_add_owner',
        autospec=True,
    ) as mock_handle_add_owner, mock.patch(
        'syncr_backend.network.handle_frontend.handle_delete_drop',
        autospec=True,
    ) as mock_handle_delete_drop, mock.patch(
        'syncr_backend.network.handle_frontend.handle_get_owned_drops',
        autospec=True,
    ) as mock_handle_get_owned_drops, mock.patch(
        'syncr_backend.network.handle_frontend.handle_get_selected_drops',
        autospec=True,
    ) as mock_handle_get_selected_drops, mock.patch(
        'syncr_backend.network.handle_frontend.handle_get_subscribed_drops',
        autospec=True,
    ) as mock_handle_get_subscribed_drops, mock.patch(
        'syncr_backend.network.handle_frontend.handle_input_subscribe_drop',
        autospec=True,
    ) as mock_handle_input_subscribe_drop, mock.patch(
        'syncr_backend.network.handle_frontend.handle_initialize_drop',
        autospec=True,
    ) as mock_handle_initialize_drop, mock.patch(
        'syncr_backend.network.handle_frontend.handle_remove_file',
        autospec=True,
    ) as mock_handle_remove_file, mock.patch(
        'syncr_backend.network.handle_frontend.handle_remove_owner',
        autospec=True,
    ) as mock_handle_remove_owner, mock.patch(
        'syncr_backend.network.handle_frontend.handle_share_drop',
        autospec=True,
    ) as mock_handle_share_drop, mock.patch(
        'syncr_backend.network.handle_frontend.handle_transfer_ownership',
        autospec=True,
    ) as mock_handle_transfer_ownership, mock.patch(
        'syncr_backend.network.handle_frontend.handle_unsubscribe',
        autospec=True,
    ) as mock_handle_unsubscribe:


        mock_handle_add_file.assert_not_called()
        mock_handle_add_owner.assert_not_called()
        mock_handle_delete_drop.assert_not_called()
        mock_handle_get_owned_drops.assert_not_called()
        mock_handle_get_selected_drops.assert_not_called()
        mock_handle_get_subscribed_drops.assert_not_called()
        mock_handle_input_subscribe_drop.assert_not_called()
        mock_handle_initialize_drop.assert_not_called()
        mock_handle_remove_owner.assert_not_called()
        mock_handle_remove_file.assert_not_called()
        mock_handle_share_drop.assert_not_called()
        mock_handle_transfer_ownership.assert_not_called()
        mock_handle_unsubscribe.assert_not_called()


        request = {
            'action': ACTION_ADD_FILE,
        }
        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_add_file.assert_called_once()

        request = {
            'action': ACTION_ADD_OWNER,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_add_owner.assert_called_once()

        request = {
            'action': ACTION_DELETE_DROP,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_delete_drop.assert_called_once()

        request = {
            'action': ACTION_GET_OWNED_DROPS,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_get_owned_drops.assert_called_once()

        request = {
            'action': ACTION_GET_SUB_DROPS,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_get_subscribed_drops.assert_called_once()

        request = {
            'action': ACTION_GET_SELECT_DROPS,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_get_selected_drops.assert_called_once()

        request = {
            'action': ACTION_INPUT_DROP_TO_SUBSCRIBE_TO,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_input_subscribe_drop.assert_called_once()

        request = {
            'action': ACTION_INITIALIZE_DROP,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_initialize_drop.assert_called_once()

        request = {
            'action': ACTION_REMOVE_FILE,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_remove_file.assert_called_once()

        request = {
            'action': ACTION_REMOVE_OWNER,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_remove_owner.assert_called_once()

        request = {
            'action': ACTION_SHARE_DROP,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_share_drop.assert_called_once()

        request = {
            'action': ACTION_TRANSFER_OWNERSHIP,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_transfer_ownership.assert_called_once()

        request = {
            'action': ACTION_UNSUBSCRIBE,
        }

        asyncio.get_event_loop().run_until_complete(
            handle_frontend_request(request, conn),
        )
        mock_handle_unsubscribe.assert_called_once()
"""
