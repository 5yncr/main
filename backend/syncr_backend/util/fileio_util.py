import fnmatch
import os
from typing import Iterator
from typing import List
from typing import Tuple

from syncr_backend.constants import DEFAULT_CHUNK_SIZE
from syncr_backend.constants import DEFAULT_IGNORE
from syncr_backend.util import crypto_util


def write_chunk(
    filepath: str, position: int, contents: bytes, chunk_hash: bytes,
    chunk_size: int=DEFAULT_CHUNK_SIZE,
) -> None:
    """Takes a filepath, position, contents, and contents hash and writes it to
    a file correctly.  Assumes the file has been created.  Will check the hash,
    and raise a VerificationException if the provided chunk_hash doesn't match.
    May raise relevant IO exceptions.

    :param filepath: the path of the file to write to
    :param position: the posiiton in the file to write to
    :param contents: the contents to write
    :param chunk_hash: the expected hash of contents
    :param chunk_size: (optional) override the chunk size, used to calculate
    the position in the file
    :return: None
    """
    if crypto_util.hash(contents) != chunk_hash:
        raise crypto_util.VerificationException()

    with open(filepath, 'wb') as f:
        pos_bytes = position * chunk_size
        f.seek(pos_bytes)
        f.write(contents)


def read_chunk(
    filepath: str, position: int, chunk_size: int=DEFAULT_CHUNK_SIZE,
) -> Tuple[bytes, bytes]:
    """Reads a chunk for a file, returning the contents and its hash.  May
    raise relevant IO exceptions

    :param filepath: the path of the file to read from
    :param position: where to read from
    :param chunk_size: (optional) override the chunk size
    :return: a double of (contents, hash), both bytes
    """
    with open(filepath, 'rb') as f:
        pos_bytes = position * chunk_size
        f.seek(pos_bytes)
        data = f.read(chunk_size)

    h = crypto_util.hash(data)
    return (data, h)


def create_file(
    filepath: str, size_bytes: int,
) -> None:
    """Create a file at filepath of the correct size. May raise relevant IO
    exceptions

    :param filepath: where to create the file
    :param size: the size to allocate
    :return: None
    """
    with open(filepath, 'rb') as f:
        f.truncate(size_bytes)


def walk_with_ignore(
    path: str, ignore: List[str],
) -> Iterator[Tuple[str, str]]:
    """Walks the files in a directory, while filtering anything that should be
    ignored.  Implemented on top of os.walk, but instead returns an iterator
    over (dirpath, filename)

    :param path: The path to walk
    :param ignore: Patterns to ignore
    :return: An iterator of (dirpath, filename) that are in path but not ignore
    """
    ignore += DEFAULT_IGNORE
    for (dirpath, _, filenames) in os.walk(path):
        if any([fnmatch.fnmatch(dirpath, i) for i in ignore]):
            continue
        for name in filenames:
            if any([fnmatch.fnmatch(name, i) for i in ignore]):
                continue
            full_name = os.path.join(dirpath, name)
            if any([fnmatch.fnmatch(full_name, i) for i in ignore]):
                continue
            yield (dirpath, name)
