#!/usr/bin/env python
import base64
import datetime
import os
import socket
import sys
from collections import defaultdict
from socket import SHUT_RDWR

import bencode
from syncr_backend.constants import DEFAULT_BUFFER_SIZE
from syncr_backend.constants import DROP_ID_BYTE_SIZE
from syncr_backend.constants import NODE_ID_BYTE_SIZE
from syncr_backend.constants import TRACKER_DROP_AVAILABILITY_TTL
from syncr_backend.constants import TRACKER_DROP_IP_INDEX
from syncr_backend.constants import TRACKER_DROP_NODE_INDEX
from syncr_backend.constants import TRACKER_DROP_PORT_INDEX
from syncr_backend.constants import TRACKER_DROP_TIMESTAMP_INDEX
from syncr_backend.constants import TRACKER_ERROR_RESULT
from syncr_backend.constants import TRACKER_OK_RESULT
from syncr_backend.constants import TRACKER_REQUEST_GET_KEY
from syncr_backend.constants import TRACKER_REQUEST_GET_PEERS
from syncr_backend.constants import TRACKER_REQUEST_POST_KEY
from syncr_backend.constants import TRACKER_REQUEST_POST_PEER
from syncr_backend.util.crypto_util import hash

from syncr_tracker.constants import PUB_KEYS_DIRECTORY


drop_availability = defaultdict(list)


# Tracker request structure
#  {
#     'request_type': int,
#     'drop_id' or 'node_id': appropriate sized id,
#     'data': public 4096 key
#             or tuple [node_id, ip, port]
#  }


def handle_request(conn, request):
    function_map = {
        TRACKER_REQUEST_GET_KEY: retrieve_public_key,
        TRACKER_REQUEST_POST_KEY: request_post_node_id,
        TRACKER_REQUEST_GET_PEERS: retrieve_drop_info,
        TRACKER_REQUEST_POST_PEER: request_post_drop_id,
    }
    if not ('request_type' in request):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'request_type missing',
        )
    elif request['request_type'] in function_map:
        t = request['request_type']
        handle_function = function_map[t]

        handle_function(conn, request)
    else:
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'Invalid request type',
        )


def retrieve_drop_info(conn, request):
    """
    Retrieves all current info related to a drop id.
    :param conn: TCP socket connection between server and client.
    :param request: request as received
    :return: list of node ip port tuples without timestamps to the client.
    """
    if not ('drop_id' in request):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'drop_id missing',
        )
    elif not verify_size(request['drop_id'], DROP_ID_BYTE_SIZE):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'drop_id incorrect size',
        )
    elif request['drop_id'] not in drop_availability:
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'Drop does not exist or is currently unavailable',
        )
    else:
        drop_id = request['drop_id']
        truncated_list = []
        trim_expired_tuples(drop_id)
        for tup in drop_availability[drop_id]:
            truncated_tuple = (
                tup[TRACKER_DROP_NODE_INDEX],
                tup[TRACKER_DROP_IP_INDEX], tup[TRACKER_DROP_PORT_INDEX],
            )
            truncated_list.append(truncated_tuple)

        send_server_response(
            conn, TRACKER_OK_RESULT, 'The following data belongs '
                                     'to given Drop ID',
            truncated_list,
        )


def trim_expired_tuples(key):
    """
    Removes all expired tuples (i.e. tuples that have existed
    for longer than five minutes) from the list of the key.
    :param key: The drop id associated with the tuple list.
    :return: A list of tuples that have existed for less than five minutes.
    """
    for tup in drop_availability[key]:
        if (datetime.datetime.now() -
                datetime.timedelta(seconds=TRACKER_DROP_AVAILABILITY_TTL)) > \
                tup[TRACKER_DROP_TIMESTAMP_INDEX]:
            drop_availability[key].remove(tup)


def retrieve_public_key(conn, request):
    """
    Retrieves the public key paired with the inputted node id.
    :param conn: TCP socket connection between server and client
    :param request: request dict as recieved
    :return: Message is sent to client with public key, if available
    """
    if not ('node_id' in request):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'node_id missing',
        )
    elif not os.path.exists(PUB_KEYS_DIRECTORY):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'Public key directory does not exist',
        )
    elif not verify_size(request['node_id'], NODE_ID_BYTE_SIZE):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'node_id incorrect size',
        )
    else:
        node_id = request['node_id']
        len_dir_name = len(PUB_KEYS_DIRECTORY)
        file_name = generate_node_key_file_name(node_id)
        files = os.listdir(PUB_KEYS_DIRECTORY)

        if file_name[len_dir_name:] not in files:
            send_server_response(
                conn, TRACKER_ERROR_RESULT,
                'Public key file does not exist for given Node ID',
            )
        else:
            with open(file_name, 'rb') as pub_file:
                public_key = pub_file.read()
                send_server_response(
                    conn, TRACKER_OK_RESULT,
                    'Public key of given Node ID found', public_key,
                )


def request_post_node_id(conn, request):
    """
    Adds the pubkey to disk if it is a legal pairing
    :param conn: TCP socket connection between server and client
    :param request: request as received with assumed structure of
            Tracker request structure
            {
                'request_type': int,
                'drop_id' or 'node_id': appropriate sized id,
                'data': public 4096 key
                or tuple [node_id, ip, port]
            }
    :return:
    """
    if not ('node_id' in request):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'node_id missing',
        )
    elif not verify_size(request['node_id'], NODE_ID_BYTE_SIZE):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'node_id incorrect size',
        )
    elif request['node_id'] == hash(request['data'].encode('utf-8')):
        add_node_key_pairing(request)
        print('Node/Key pairing added')
        send_server_response(
            conn, TRACKER_OK_RESULT,
            'Node/Key pairing added',
        )
    else:
        print('Node/Key pairing rejected for mismatch key')
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'Node/Key pairing rejected for mismatch key',
        )


def add_node_key_pairing(request):
    """
    Adds pubkey to disk
    :param request: request as received with assumed structure of
            Tracker request structure
            {
                'request_type': TRACKER_REQUEST_POST_KEY,
                'node_id': appropriate sized id,
                'data': public 4096 key
            }
    :return:
    """
    if not os.path.exists('pub_keys/'):
        os.makedirs('pub_keys/')
    with open(
        generate_node_key_file_name(request['node_id']),
        'wb',
    ) as pub_file:
        pub_file.write(request['data'].encode('utf-8'))


def verify_size(key, size):
    """
    Simple abstraction over checking key sizes
    :param key: byte[] - node or drop id
    :param size: int - constant value for given sizes
    :return: boolean - whether the size matches
    """
    return len(key) == size


def request_post_drop_id(conn, request):
    """
    Adds node, ip, port tuples to appropriate drops in hashmap
    :param conn: TCP socket connection between server and client
    :param request: request as received with assumed structure of
            Tracker request structure
            {
                'request_type': TRACKER_REQUEST_POST_PEER,
                'node_id': appropriate sized id,
                'data': public [node_id, ip, port]
            }
    :return:
    """
    if not ('drop_id' in request):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'drop_id missing',
        )
    elif not verify_size(request['drop_id'], DROP_ID_BYTE_SIZE):
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'drop_id incorrect size',
        )
    elif type(request['data']) is not list or \
            len(request['data']) != 3:
        print('Invalid node, IP, port tuple')
        send_server_response(
            conn, TRACKER_ERROR_RESULT,
            'Invalid node, IP, port tuple',
        )
        return
    request['data'].append(datetime.datetime.now())
    drop_availability[request['drop_id']].append(
        request['data'],
    )
    print(
        'Drop Availability Updated - ', request['drop_id'],
        '\n\tNode: ', request['data'][TRACKER_DROP_NODE_INDEX],
        '\n\tIP: ', request['data'][TRACKER_DROP_IP_INDEX],
        '\n\tPort: ', request['data'][TRACKER_DROP_PORT_INDEX],
    )
    send_server_response(conn, TRACKER_OK_RESULT, 'Drop availability updated')


def generate_node_key_file_name(node_id):
    """
    Takes a node key provides where it's public key is stored
    :param node_id:
    :return: public key file
    """
    return os.path.join(
        'pub_keys', '{}.pub'.format(
            base64.b64encode(node_id, altchars=b'+-').decode('utf-8'),
        ),
    )


def send_server_response(conn, result, msg, data=''):
    """
    Sends a dict as a server response with the result and msg
    :param conn: TCP socket connection between server and client
    :param result: 'OK' | 'ERROR'
    :param msg: text of what happened
    :param data: Data to be sent back to the user.
    :return:
    """
    conn.send(bencode.encode({
        'result': result,
        'message': msg,
        'data': data,
    }))
    conn.shutdown(SHUT_RDWR)


def main():
    """
    Runs the server loop taking in GET and POST requests and handling them
    accordingly
    :return:
    """
    tcp_ip = sys.argv[1]
    tcp_port = sys.argv[2]
    buffer_size = DEFAULT_BUFFER_SIZE

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((tcp_ip, int(tcp_port)))
    s.listen(5)

    while 1:
        conn, addr = s.accept()
        print('Connection address:', addr)
        request = b''
        while 1:
            data = conn.recv(buffer_size)
            if not data:
                break
            else:
                request += data
        print('Data recieved')
        try:
            request = bencode.decode(request)
            handle_request(conn, request)
        except Exception:
            print("Bad request recieved; continuing")
            pass
        conn.close()


if __name__ == '__main__':
    main()
