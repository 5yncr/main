import os
import shutil
from pathlib import Path
from typing import Optional

from syncr_backend import crypto_util
from syncr_backend.constants import DEFAULT_INIT_DIR


def force_initialize_node(init_directory: Optional[str]=None) -> None:
    """
    Initialize new node in .node directory
    and overwrite existing .node dir

    :param init_directory: directory where node files are stored,
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    full_directory = get_full_init_directory(init_directory)

    if os.path.exists(full_directory):
        shutil.rmtree(full_directory)

    initialize_node(full_directory)


def delete_node_directory(init_directory: Optional[str]=None) -> None:
    """
    Deletes the .node (or passed in) directory and all of its contents

    :param init_directory: directory where node files are stored,
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    full_directory = get_full_init_directory(init_directory)

    if os.path.exists(full_directory):
        shutil.rmtree(full_directory)


def is_node_initialized(init_directory: Optional[str]=None) -> bool:
    """
    Checks if node is node is initialized

    :param init_directory: directory where node files are stored,
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    :return: whether a node directory exists
    """
    full_directory = get_full_init_directory(init_directory)
    return os.path.exists(full_directory)


def initialize_node(init_directory: Optional[str]=None) -> None:
    """
    Initialize new node in .node directory
    Create the private key file

    :param init_directory: directory where node files are stored,
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    full_directory = get_full_init_directory(init_directory)

    if os.path.exists(full_directory):
        raise FileExistsError

    os.mkdir(full_directory)
    private_key = crypto_util.generate_private_key()
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

    :param init_directory: directory where node files are stored,
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    full_directory = get_full_init_directory(init_directory)

    if os.path.exists(os.path.join(full_directory, "private_key.pem")):
        raise FileExistsError

    with open(
        os.path.join(full_directory, "private_key.pem"),
        "wb",
    ) as keyfile:
        keyfile.write(crypto_util.dump_private_key(key))
        keyfile.close()


def load_private_key_from_disk(
    init_directory: Optional[str]=None,
) -> crypto_util.rsa.RSAPrivateKey:
    """
    Load Private Key (and public key) from file

    :param init_directory: directory where node files are stored,
    init_directory of none uses ~/.{DEFAULT_INIT_DIR}
    """
    full_directory = get_full_init_directory(init_directory)

    with open(
        os.path.join(full_directory, "private_key.pem"),
        "rb",
    ) as keyfile:
        return crypto_util.load_private_key(keyfile.read())
