import socket as s

import bencode

HANDLE_FRONTEND_REQUEST = 'handle_frontend_request'
HOST = '127.0.0.1'
PORT = '5005'


class Socket:
    """
    Socket class used to communicate with backend
    """

    def __init__(self, sock=None):
        if sock is None:
            self.sock = s.socket(s.AF_INET, s.SOCK_STREAM)
            self.sock.settimeout(10.0)
        else:
            self.sock = sock

    def connect(self):
        """
        Connect to specified connection
        :return: error message or None
        """
        try:
            self.sock.connect((HOST, PORT))
        except Exception as e:
            return e
        return None

    def send_message(self, msg):
        """
        Send a connection to backend over a socket
        :param msg: dictionary of info to be sent to backend
        :return:
        """

        msg['request_type'] = HANDLE_FRONTEND_REQUEST

        # Convert dictionary to send-able type
        data_string = bencode.encode(msg)

        # Send data to backend
        sent = self.sock.sendall(data_string)
        if sent is not None:
            self.sock.close()
            raise RuntimeError("socket connection broke")

    def receive_message(self):
        """
        Listen for a return message from
        :return:
        """
        chunks = []

        while True:
            try:
                chunk = self.sock.recv(2048)
            except Exception as e:
                print("Receiving Message error:", e)
                self.close()
                return None
            if chunk == '':
                break
            chunks.append(chunk)

        # Un-pickle data
        data_string = b''.join(chunks)
        response = bencode.decode(data_string)

        # Example response for initial UI setup
        # response = {
        #     'drop_id': message.get('drop_id'),
        #     'drop_name': message.get('drop_name'),
        #     'file_name': message.get('file_name'),
        #     'file_path': message.get('file_path'),
        #     'action': message.get('action'),
        #     'message': "Generic Message For " + message.get('action'),
        #     'success': True,
        #     'requested_drops': (
        #         {
        #             'drop_id': 'o1',
        #             'name': 'O_Drop_1',
        #             'version': None,
        #             'previous_versions': [],
        #             'primary_owner': 'p_owner_id',
        #             'other_owners': ["owner1", "owner2"],
        #             'signed_by': 'owner_id',
        #             'files': [
        #                 {'name': 'FileOne'},
        #                 {'name': 'FileTwo'},
        #                 {'name': 'FileThree'},
        #                 {'name': 'FileFour'},
        #                 {'name': 'Folder'},
        #             ],
        #         },
        #         {
        #             'drop_id': 'o2',
        #             'name': 'O_Drop_2',
        #             'version': None,
        #             'previous_versions': [],
        #             'primary_owner': 'owner_id',
        #             'other_owners': [],
        #             'signed_by': 'owner_id',
        #             'files': [],
        #         },
        #     ),
        # }

        return response

    def close(self):
        """
        Close the current socket
        :return:
        """
        if self.sock is not None:
            self.sock.close()
            self.sock = None
