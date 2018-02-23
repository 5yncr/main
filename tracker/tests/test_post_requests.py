import base64
import hashlib
from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import Mock

import bencode

from syncr_tracker.constants import OK_RESULT
from syncr_tracker.tracker import generate_node_key_file_name
from syncr_tracker.tracker import handle_post
from syncr_tracker.tracker import send_server_response


def test_handle_post():
    h = hashlib.sha256(b'foobar')
    node_id = h.digest()

    i = hashlib.sha256(b'biaazquxx')
    drop_id = h.digest() + i.digest()

    conn = Mock()
    conn.send = MagicMock()
    with mock.patch(
        'syncr_tracker.tracker.request_post_node_id', autospec=True,
    ) as mock_request_post_node_id, mock.patch(
        'syncr_tracker.tracker.request_post_drop_id', autospec=True,
    ) as mock_request_post_drop_id, mock.patch(
        'syncr_tracker.tracker.send_server_response', autospec=True,
    ) as mock_send_server_response:

        request = ['POST', node_id, None]
        handle_post(conn, request)
        mock_request_post_node_id.assert_called_once()
        mock_request_post_drop_id.assert_not_called()
        mock_send_server_response.assert_not_called()

        request = ['POST', drop_id, None]
        handle_post(conn, request)
        mock_request_post_node_id.assert_called_once()
        # Does not get called a 2nd time
        mock_request_post_drop_id.assert_called_once()
        mock_send_server_response.assert_not_called()

        request = ['POST', b'\00', None]
        handle_post(conn, request)
        mock_request_post_node_id.assert_called_once()
        # Does not get called a 2nd time
        mock_request_post_drop_id.assert_called_once()
        # Does not get called a 2nd time
        mock_send_server_response.assert_called_once()


def test_generate_node_key_file_name():
    h = hashlib.sha256(b'foobar')
    print(h.digest())
    node_id = h.digest()

    file_name = generate_node_key_file_name(node_id)

    assert file_name == 'pub_keys/' + \
                        base64.b64encode(node_id, altchars=b'+-')\
        .decode('utf-8') + '.pub'


def test_send_server_response():
    conn = Mock()
    conn.send = MagicMock()
    send_server_response(conn, OK_RESULT, 'Message', 'a')

    conn.send.assert_called_with(bencode.encode(
        {
            'result': OK_RESULT,
            'message': 'Message',
            'data': 'a',
        },
    ))
