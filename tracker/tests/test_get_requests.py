import datetime
import hashlib
from unittest import mock
from unittest.mock import MagicMock
from unittest.mock import Mock

from syncr_tracker.tracker import drop_availability
from syncr_tracker.tracker import handle_get
from syncr_tracker.tracker import trim_expired_tuples


def test_handle_get():
    h = hashlib.sha256(b'foobar')
    node_id = h.digest()

    i = hashlib.sha256(b'biaazquxx')
    drop_id = h.digest() + i.digest()

    conn = Mock()
    conn.send = MagicMock()
    with mock.patch(
        'syncr_tracker.tracker.retrieve_drop_info', autospec=True,
    ) as mock_retrieve_drop_info, mock.patch(
        'syncr_tracker.tracker.retrieve_public_key', autospec=True,
    ) as mock_retrieve_public_key, mock.patch(
        'syncr_tracker.tracker.send_server_response', autospec=True,
    ) as mock_send_server_response:

        request = ['GET', node_id, None]
        handle_get(conn, request)
        mock_retrieve_public_key.assert_called_once()
        mock_retrieve_drop_info.assert_not_called()
        mock_send_server_response.assert_not_called()

        request = ['GET', drop_id, None]
        handle_get(conn, request)
        mock_retrieve_drop_info.assert_called_once()
        mock_retrieve_public_key.assert_called_once()
        mock_send_server_response.assert_not_called()

        request = ['GET', b'\00', None]
        handle_get(conn, request)
        mock_retrieve_drop_info.assert_called_once()
        mock_retrieve_public_key.assert_called_once()
        mock_send_server_response.assert_called_once()


def test_trim_expired_tuples():
    tup_pass = (
        'NODE_PASS', 'IP_PASS', 'PORT_PASS',
        datetime.datetime.now() - datetime.timedelta(minutes=2),
    )
    tup_pass2 = (
        'NODE_PASS', 'IP_PASS', 'PORT_PASS',
        datetime.datetime.now() - datetime.timedelta(minutes=4),
    )
    tup_fail = (
        'NODE_FAIL', 'IP_FAIL', 'PORT_FAIL',
        datetime.datetime.now() - datetime.timedelta(days=1),
    )
    tup_fail2 = (
        'NODE_FAIL', 'IP_FAIL', 'PORT_FAIL',
        datetime.datetime.now() -
        datetime.timedelta(minutes=5, seconds=10),
    )

    drop_availability['test_key'] = [tup_pass, tup_fail, tup_pass2, tup_fail2]

    trim_expired_tuples('test_key')

    assert len(drop_availability['test_key']) == 2

    for tup in drop_availability['test_key']:
        assert len(tup) == 4
        assert tup[0] == 'NODE_PASS'
        assert tup[1] == 'IP_PASS'
        assert tup[2] == 'PORT_PASS'
