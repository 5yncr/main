import hashlib
import os
from typing import BinaryIO
from typing import List
from typing import Optional

import bencode  # type: ignore

from syncr_backend import crypto_util
from syncr_backend.constants import DEFAULT_CHUNK_SIZE
from syncr_backend.constants import DEFAULT_FILE_METADATA_LOCATION


class FileMetadata(object):

    # TODO: define PROTOCOL_VERSION somewhere
    def __init__(
        self, hashes: List[bytes], file_hash: bytes, file_length: int,
        chunk_size: int=DEFAULT_CHUNK_SIZE, protocol_version: int=1,
    ) -> None:
        self.hashes = hashes
        self.file_hash = file_hash
        self.file_length = file_length
        self.chunk_size = chunk_size
        self._protocol_version = protocol_version

    def encode(self) -> bytes:
        """Make the bencoded file that will be transfered on the wire

        :return: bytes that is the file
        """
        d = {
            "protocol_version": self._protocol_version,
            "chunk_size": self.chunk_size,
            "file_length": self.file_length,
            "file_hash": self.file_hash,
            "chunks": self.hashes,
        }
        return bencode.encode(d)

    def write_file(
        self, metadata_location: str=DEFAULT_FILE_METADATA_LOCATION,
    ) -> None:
        """Write this file metadata to a file

        :param metadata_location: where to save it
        """
        file_name = crypto_util.b64encode(self.file_hash).decode("utf-8")
        if not os.path.exists(metadata_location):
            os.makedirs(metadata_location)
        with open(os.path.join(metadata_location, file_name), 'wb') as f:
            f.write(self.encode())

    @staticmethod
    def read_file(
        file_hash: bytes,
        metadata_location: str=DEFAULT_FILE_METADATA_LOCATION,
    ) -> Optional['FileMetadata']:
        """Read a file metadata file and return FileMetadata

        :param file_hash: The hash of the file to read
        :return: a FileMetadata object or None if it does not exist
        """
        file_name = crypto_util.b64encode(file_hash).decode("utf-8")
        if not os.path.exists(os.path.join(metadata_location, file_name)):
            return None

        with open(os.path.join(metadata_location, file_name), 'rb') as f:
            b = b''
            while True:
                data = f.read(65536)
                if not data:
                    break
                b += data
            return FileMetadata.decode(b)

    @staticmethod
    def decode(data: bytes) -> 'FileMetadata':
        """Decode a bencoded byte array into a FileMetadata object

        :param data: bencoded byte array of file metadata
        :return: FileMetadata object
        """
        d = bencode.decode(data)
        return FileMetadata(
            hashes=d['chunks'], file_hash=d['file_hash'],
            file_length=d['file_length'], chunk_size=d['chunk_size'],
            protocol_version=d['protocol_version'],
        )


def file_hashes(
    f: BinaryIO, chunk_size: int=DEFAULT_CHUNK_SIZE,
) -> List[bytes]:
    """Given an open file in mode 'rb', hash its chunks and return a list of
    the hashes

    :param f: open file
    :param chunk_size: the chunk size to use, probably don't change this
    :return: list of hashes
    """
    hashes = []

    b = f.read(chunk_size)
    while len(b) > 0:
        hashes.append(crypto_util.hash(b))

        b = f.read(chunk_size)

    return hashes


def hash_file(f: BinaryIO) -> bytes:
    """Hash a file

    :param f: An open file, seeked to 0
    :return: The hash bytes
    """
    sha = hashlib.sha256()
    while True:
        data = f.read(65536)
        if not data:
            break
        sha.update(data)
    return sha.digest()


def make_file_metadata(filename: str) -> FileMetadata:
    """Given a file name, return a FileMetadata object

    :param filename: The name of the file to open and read
    :return: FileMetadata object
    """
    f = open(filename, 'rb')
    size = os.path.getsize(f.name)

    hashes = file_hashes(f)
    f.seek(0)
    file_hash = hash_file(f)

    return FileMetadata(hashes, file_hash, size)
