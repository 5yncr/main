"""The file metadata object and related functions"""
import hashlib
import logging
import os
from math import ceil
from typing import List
from typing import Optional
from typing import Set  # noqa

import aiofiles  # type: ignore
import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_CHUNK_SIZE
from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import DEFAULT_FILE_METADATA_LOCATION
from syncr_backend.metadata import drop_metadata
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.util import crypto_util
from syncr_backend.util import fileio_util
from syncr_backend.util.async_util import async_cache
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


class FileMetadata(object):
    """A representation of a file metadata file"""

    # TODO: define PROTOCOL_VERSION somewhere
    def __init__(
        self, hashes: List[bytes], file_id: bytes, file_length: int,
        drop_id: bytes, file_name: Optional[str]=None,
        chunk_size: int=DEFAULT_CHUNK_SIZE, protocol_version: int=1,
    ) -> None:
        self.hashes = hashes
        self.file_id = file_id
        self.file_length = file_length
        self.chunk_size = chunk_size
        self._protocol_version = protocol_version
        self._downloaded_chunks = None  # type: Optional[Set[int]]
        self.num_chunks = ceil(file_length / chunk_size)
        self.drop_id = drop_id
        self._save_dir = None  # type: Optional[str]
        self.file_name = file_name

    @property
    def log(self) -> logging.Logger:
        return get_logger(
            '.'.join([
                __name__, self.__class__.__name__,
                crypto_util.b64encode(self.file_id).decode('utf-8'),
            ]),
        )

    def encode(self) -> bytes:
        """Make the bencoded file that will be transfered on the wire

        :return: bytes that is the file
        """
        d = {
            "protocol_version": self._protocol_version,
            "chunk_size": self.chunk_size,
            "file_length": self.file_length,
            "file_id": self.file_id,
            "chunks": self.hashes,
            "drop_id": self.drop_id,
        }
        return bencode.encode(d)

    async def write_file(
        self, metadata_location: str,
    ) -> None:
        """Write this file metadata to a file

        :param metadata_location: where to save it
        """
        self.log.debug("writing file")
        file_name = crypto_util.b64encode(self.file_id).decode("utf-8")
        if not os.path.exists(metadata_location):
            os.makedirs(metadata_location)
        async with aiofiles.open(
            os.path.join(metadata_location, file_name), 'wb',
        ) as f:
            await f.write(self.encode())

    @staticmethod
    @async_cache(maxsize=1024)
    async def read_file(
        file_id: bytes,
        metadata_location: str,
        file_name: str,
    ) -> Optional['FileMetadata']:
        """Read a file metadata file and return FileMetadata

        :param file_id: The hash of the file to read
        :param metadata_location: drop location with default metadata location
        :return: a FileMetadata object or None if it does not exist
        """
        logger.debug("reading from file")
        file_name = crypto_util.b64encode(file_id).decode("utf-8")
        if not os.path.exists(os.path.join(metadata_location, file_name)):
            return None

        async with aiofiles.open(
            os.path.join(metadata_location, file_name), 'rb',
        ) as f:
            b = b''
            while True:
                data = await f.read()
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
            hashes=d['chunks'], file_id=d['file_id'],
            file_length=d['file_length'], chunk_size=d['chunk_size'],
            drop_id=d['drop_id'],
            protocol_version=d['protocol_version'],
        )

    @property
    async def save_dir(self) -> str:
        """Get the save dir

        :return: Where the drop is saved
        """
        if self._save_dir is None:
            self._save_dir = await drop_metadata.get_drop_location(
                self.drop_id,
            )
        return self._save_dir

    async def _calculate_downloaded_chunks(self) -> Set[int]:
        """Figure out what chunks are complete, similar to "hashing" in some
        bittorrent clients

        :return: A set of chunk ids already downloaded
        """
        self.log.debug("calculating downloaded chunks")
        # TODO: what if not exist
        dm = await DropMetadata.read_file(
            id=self.drop_id,
            metadata_location=os.path.join(
                (await self.save_dir), DEFAULT_DROP_METADATA_LOCATION,
            ),
        )
        if dm is None:
            return set()
        if self.file_name is None:
            file_name = dm.get_file_name_from_id(self.file_id)
        else:
            file_name = self.file_name
        full_name = os.path.join((await self.save_dir), file_name)
        downloaded_chunks = set()  # type: Set[int]
        for chunk_idx in range(self.num_chunks):
            _, h = await fileio_util.read_chunk(
                filepath=full_name,
                position=chunk_idx,
                chunk_size=self.chunk_size,
            )
            if h == self.hashes[chunk_idx]:
                downloaded_chunks.add(chunk_idx)
        self.log.debug("calculated downloaded chunks: %s", downloaded_chunks)
        return downloaded_chunks

    @property
    async def downloaded_chunks(self) -> Set[int]:
        """Property of which chunks are downloaded
        Note: does not automatically update, call `finish_chunk` to do that

        :return: A set of chunk ids that are downloaded
        """
        if self._downloaded_chunks is None:
            self._downloaded_chunks = await self._calculate_downloaded_chunks()
        return self._downloaded_chunks

    @property
    async def needed_chunks(self) -> Set[int]:
        """The oposite of downloaded chunks, what chunks are needed

        :return: A set of chunk ids that are needed
        """
        all_chunks = {x for x in range(self.num_chunks)}
        return all_chunks - (await self.downloaded_chunks)

    async def finish_chunk(self, chunk_id: int) -> None:
        """Mark chunk finished

        :param chunk_id: The chunk that's done
        """
        self.log.debug("finishing chunk %s", chunk_id)
        (await self.downloaded_chunks).add(chunk_id)


async def file_hashes(
    f: aiofiles.threadpool.AsyncBufferedReader,
    chunk_size: int=DEFAULT_CHUNK_SIZE,
) -> List[bytes]:
    """Given an open file in mode 'rb', hash its chunks and return a list of
    the hashes

    :param f: open file
    :param chunk_size: the chunk size to use, probably don't change this
    :return: list of hashes
    """
    hashes = []

    b = await f.read(chunk_size)
    while len(b) > 0:
        hashes.append(await crypto_util.hash(b))

        b = await f.read(chunk_size)

    return hashes


async def hash_file(
    f: aiofiles.threadpool.AsyncBufferedReader,
) -> bytes:
    """Hash a file

    :param f: An open file, seeked to 0
    :return: The hash bytes
    """
    sha = hashlib.sha256()
    while True:
        data = await f.read()
        if not data:
            break
        sha.update(data)
    return sha.digest()


async def make_file_metadata(filename: str, drop_id: bytes) -> FileMetadata:
    """Given a file name, return a FileMetadata object

    :param filename: The name of the file to open and read
    :return: FileMetadata object
    """
    size = os.path.getsize(filename)
    async with aiofiles.open(filename, 'rb') as f:

        hashes = await file_hashes(f)
        await f.seek(0)
        file_id = await hash_file(f)

    return FileMetadata(hashes, file_id, size, drop_id)


async def get_file_metadata_from_drop_id(
    drop_id: bytes, file_id: bytes,
) -> Optional[FileMetadata]:
    """
    Gets the file metadata of a file in a drop
    :param drop_id: bytes for the drop_id that the file is part of
    :param file_id: bytes for the file_id of desired file_name
    :return Optional[FileMetadata] of the given file
    """
    drop_location = await drop_metadata.get_drop_location(drop_id)
    file_metadata_location = os.path.join(
        drop_location, DEFAULT_FILE_METADATA_LOCATION,
    )
    request_file_metadata = await FileMetadata.read_file(
        file_id=file_id,
        metadata_location=file_metadata_location,
        file_name="",
    )

    return request_file_metadata
