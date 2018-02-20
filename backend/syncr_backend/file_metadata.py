import hashlib
import os
from typing import BinaryIO
from typing import List

import bencode  # type: ignore

DEFAULT_CHUNK_SIZE = 2**23


class FileMetadata(object):

    # TODO: define PROTOCOL_VERSION somewhere
    def __init__(
        self, hashes: List[bytes], file_length: int,
        chunk_size: int=DEFAULT_CHUNK_SIZE, protocol_version: int=1,
    ) -> None:
        self.hashes = hashes
        self.file_length = file_length
        self.chunk_size = chunk_size
        self._protocol_version = protocol_version

    def encode(self) -> bytes:
        """Make the bencoded file that will be transfered on the wire

        returns: bytes that is the file
        """
        d = {
            "protocol_version": self._protocol_version,
            "chunk_size": self.chunk_size,
            "file_length": self.file_length,
            "chunks": self.hashes,
        }
        return bencode.encode(d)

    @staticmethod
    def decode(data: bytes) -> 'FileMetadata':
        d = bencode.decode(data)
        return FileMetadata(
            hashes=d['chunks'], file_length=d['file_length'],
            chunk_size=d['chunk_size'], protocol_version=d['protocol_version'],
        )


def hash_file(f: BinaryIO, chunk_size: int=DEFAULT_CHUNK_SIZE) -> List[bytes]:
    """Given an open file in mode 'rb', hash its chunks and return a list of
    the hashes

    f: open file
    chunk_size: the chunk size to use, probably don't change this
    returns: list of hashes
    """
    hashes = []

    b = f.read(chunk_size)
    while len(b) > 0:
        hashes.append(hashlib.sha256(b).digest())

        b = f.read(chunk_size)

    return hashes


def make_file_metadata(filename: str) -> FileMetadata:
    """Given a file name, return a FileMetadata object"""
    f = open(filename, 'rb')
    size = os.path.getsize(f.name)

    hashes = hash_file(f)

    return FileMetadata(hashes, size)
