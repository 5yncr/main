"""Helper functions for reading from and writing to the filesystem"""
import asyncio
import fnmatch
import json
import os
from collections import defaultdict
from typing import Any
from typing import Dict  # noqa
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple

import aiofiles  # type: ignore

from syncr_backend.constants import DEFAULT_CHUNK_SIZE
from syncr_backend.constants import DEFAULT_DPS_CONFIG_FILE
from syncr_backend.constants import DEFAULT_IGNORE
from syncr_backend.constants import DEFAULT_INCOMPLETE_EXT
from syncr_backend.external_interface.store_exceptions import \
    MissingConfigError
from syncr_backend.init.node_init import get_full_init_directory
from syncr_backend.util import crypto_util
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


write_locks = defaultdict(asyncio.Lock)  # type: Dict[str, asyncio.Lock]


async def load_config_file() -> Dict[str, Any]:
    """
    Read and parse the Drop Peer Store config

    :raises MissingConfigError: If the dps config cannot be found
    :return: Parsed dict of config file contents
    """
    init_directory = get_full_init_directory(None)
    dps_config_path = os.path.join(init_directory, DEFAULT_DPS_CONFIG_FILE)

    if not os.path.isfile(dps_config_path):
        raise MissingConfigError()

    async with aiofiles.open(dps_config_path) as f:
        config_txt = await f.read()
        config_file = json.loads(config_txt)

    return config_file


async def write_chunk(
    filepath: str, position: int, contents: bytes, chunk_hash: bytes,
    chunk_size: int=DEFAULT_CHUNK_SIZE,
) -> None:
    """
    Takes a filepath, position, contents, and contents hash and writes it to
    a file correctly.  Assumes the file has been created.  Will check the hash,
    and raise a VerificationException if the provided chunk_hash doesn't match.
    May raise relevant IO exceptions.

    If the file extension indicates the file is complete, does nothing.

    :param filepath: the path of the file to write to
    :param position: the posiiton in the file to write to
    :param contents: the contents to write
    :param chunk_hash: the expected hash of contents
    :param chunk_size: (optional) override the chunk size, used to calculate \
    the position in the file
    :raises crypto_util.VerificationException: When the hash of the provided \
            bytes does not match the provided hash
    :return: None
    """
    if is_complete(filepath):
        logger.info("file %s already done, not writing", filepath)
        return

    filepath += DEFAULT_INCOMPLETE_EXT
    computed_hash = await crypto_util.hash(contents)
    if computed_hash != chunk_hash:
        raise crypto_util.VerificationException(
            "Computed: %s, expected: %s" % (
                crypto_util.b64encode(computed_hash),
                crypto_util.b64encode(chunk_hash),
            ),
        )
    logger.debug(
        "writing chunk with filepath %s and hash %s", filepath,
        crypto_util.b64encode(chunk_hash),
    )

    await write_locks[filepath].acquire()
    async with aiofiles.open(filepath, 'r+b') as f:
        pos_bytes = position * chunk_size
        await f.seek(pos_bytes)
        await f.write(contents)
        await f.flush()
    write_locks[filepath].release()


async def read_chunk(
    filepath: str, position: int, file_hash: Optional[bytes]=None,
    chunk_size: int=DEFAULT_CHUNK_SIZE,
) -> Tuple[bytes, bytes]:
    """Reads a chunk for a file, returning the contents and its hash.  May
    raise relevant IO exceptions

    If file_hash is provided, will check the chunk that is read

    :param filepath: the path of the file to read from
    :param position: where to read from
    :param file_hash: if provided, will check the file hash
    :param chunk_size: (optional) override the chunk size
    :raises crypto_util.VerificationException: If the hash of the bytes read \
            does not match the provided hash
    :return: a double of (contents, hash), both bytes
    """
    if not is_complete(filepath):
        logger.debug("file %s not done, adding extention", filepath)
        filepath += DEFAULT_INCOMPLETE_EXT

    async with aiofiles.open(filepath, 'rb') as f:
        logger.debug("async reading %s", filepath)
        pos_bytes = position * chunk_size
        await f.seek(pos_bytes)
        data = await f.read(chunk_size)

    h = await crypto_util.hash(data)
    logger.debug("async read hash: %s", crypto_util.b64encode(h))
    if file_hash is not None:
        logger.info("input file_hash is not None, checking")
        if h != file_hash:
            raise crypto_util.VerificationException()
    return (data, h)


async def create_file(
    filepath: str, size_bytes: int,
) -> None:
    """Create a file at filepath of the correct size. May raise relevant IO
    exceptions

    If filepath exists, calling this indicates there are updates, and filepath
    gets moved to filepath + incomplete_ext

    :param filepath: where to create the file
    :param size: the size to allocate
    :return: None
    """
    new_path = filepath + DEFAULT_INCOMPLETE_EXT
    try:
        if is_complete(filepath):
            logger.info("file %s is done, moving it to be not done", filepath)
            os.replace(filepath, new_path)
    except FileNotFoundError:
        pass

    filepath = new_path
    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
    async with aiofiles.open(filepath, 'wb') as f:
        logger.debug("truncating %s ot %s bytes", filepath, size_bytes)
        await f.truncate(size_bytes)


def mark_file_complete(filepath: str) -> None:
    """Marks a file as completed by renaming it to remove the
    DEFAULT_INCOMPLETE_EXT

    May fail on some systems if the destination exists

    :param filepath: The path of the file, without the extension
    :return: None
    """
    logger.debug("marking %s done", filepath)
    if is_complete(filepath):
        logger.debug("file already done, returning")
        return

    old_file = filepath + DEFAULT_INCOMPLETE_EXT
    os.rename(old_file, filepath)


def is_complete(filepath: str) -> bool:
    """Tests if file is complete, based on its extension

    True if filepath exists, False if filepath + incomplete_ext exists
    Raises FileNotFoundError if neither exists

    :param filepath: The path to check for completion
    :raises FileNotFoundError: If neither the file nor .part file is found
    :return: Whether the file is downloaded, based on its extension
    """
    unfinished_path = filepath + DEFAULT_INCOMPLETE_EXT
    if os.path.isfile(unfinished_path):
        logger.debug("file %s is not done", unfinished_path)
        return False
    if os.path.isfile(filepath):
        logger.debug("file %s is done", filepath)
        return True
    logger.debug("file %s not found", filepath)
    raise FileNotFoundError(filepath)


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
        relpath = os.path.relpath(dirpath, path)
        if any([fnmatch.fnmatch(relpath, i) for i in ignore]):
            continue
        if any([relpath.startswith(i) for i in ignore]):
            continue
        for name in filenames:
            if any([fnmatch.fnmatch(name, i) for i in ignore]):
                continue
            full_name = os.path.join(relpath, name)
            if any([fnmatch.fnmatch(full_name, i) for i in ignore]):
                continue
            yield (dirpath, name)
