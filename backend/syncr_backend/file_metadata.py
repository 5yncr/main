import hashlib
import os
from typing import BinaryIO
from typing import List

import bencode  # type: ignore

from syncr_backend import crypto_util

DEFAULT_CHUNK_SIZE = 2**23


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
