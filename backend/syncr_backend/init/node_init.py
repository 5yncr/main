"""Functions for initializing a new node"""
import asyncio
import os
import shutil
from pathlib import Path
from typing import Optional

import aiofiles  # type: ignore

from syncr_backend.constants import DEFAULT_INIT_DIR
from syncr_backend.util import crypto_util
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


def force_initialize_node(init_directory: Optional[str]=None) -> None:
    """
    Initialize new node in .node directory
    and overwrite existing .node dir

    :param init_directory: directory where node files are stored \
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    logger.warning("forcing node initialization of %s", init_directory)
    full_directory = get_full_init_directory(init_directory)

    if os.path.exists(full_directory):
        shutil.rmtree(full_directory)

    initialize_node(full_directory)


def delete_node_directory(init_directory: Optional[str]=None) -> None:
    """
    Deletes the .node (or passed in) directory and all of its contents

    :param init_directory: directory where node files are stored \
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    full_directory = get_full_init_directory(init_directory)
    logger.info("deleting node directory %s", full_directory)

    if os.path.exists(full_directory):
        shutil.rmtree(full_directory)


def is_node_initialized(init_directory: Optional[str]=None) -> bool:
    """
    Checks if node is node is initialized

    :param init_directory: directory where node files are stored \
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    :return: whether a node directory exists
    """
    full_directory = get_full_init_directory(init_directory)
    return os.path.exists(full_directory)


def initialize_node(init_directory: Optional[str]=None) -> None:
    """
    Initialize new node in .node directory
    Create the private key file

    :param init_directory: directory where node files are stored \
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    full_directory = get_full_init_directory(init_directory)
    logger.info("initializing node in %s", full_directory)

    if os.path.exists(full_directory):
        logger.error(
            "tried to initialize over existing node dir %s", full_directory,
        )
        raise FileExistsError(full_directory)

    os.makedirs(full_directory)
    loop = asyncio.get_event_loop()
    private_key = loop.run_until_complete(crypto_util.generate_private_key())
    write_private_key_to_disk(private_key, full_directory)


def get_full_init_directory(init_directory: Optional[str]=None) -> str:
    """
    Joins the init_directory with the default home directory if init_directory
    is None, else just returns

    :return: The joined directory
    """
    if init_directory is None:
        return os.path.join(str(Path.home()), DEFAULT_INIT_DIR)
    return init_directory


def write_private_key_to_disk(
    key: crypto_util.rsa.RSAPrivateKey, init_directory: Optional[str]=None,
) -> None:
    """
    Write Private Key (and public key attached) to file

    :param init_directory: directory where node files are stored \
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    logger.debug("writing private key")
    full_directory = get_full_init_directory(init_directory)

    if os.path.exists(os.path.join(full_directory, "private_key.pem")):
        raise FileExistsError

    with open(
        os.path.join(full_directory, "private_key.pem"),
        "wb",
    ) as keyfile:
        keyfile.write(crypto_util.dump_private_key(key))
        keyfile.close()


async def load_private_key_from_disk(
    init_directory: Optional[str]=None,
) -> crypto_util.rsa.RSAPrivateKey:
    """
    Load Private Key (and public key) from file

    :param init_directory: directory where node files are stored \
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    :return: A private key
    """
    logger.debug("reading private key")
    full_directory = get_full_init_directory(init_directory)

    async with aiofiles.open(
        os.path.join(full_directory, "private_key.pem"),
        "rb",
    ) as keyfile:
        key_bytes = await keyfile.read()
        return crypto_util.load_private_key(key_bytes)
