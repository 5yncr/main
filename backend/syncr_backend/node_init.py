import os
import shutil

from syncr_backend import crypto_util
from syncr_backend.constants import DEFAULT_INIT_DIR


def force_initialize_node(init_directory: str=DEFAULT_INIT_DIR) -> None:
    """Initialize new node in .node directory
    and overwrite existing .node dir"""

    if os.path.exists(init_directory):
        shutil.rmtree(init_directory)

    initialize_node(init_directory)


def is_node_initialized(init_directory: str=DEFAULT_INIT_DIR) -> bool:
    return os.path.exists(init_directory)


def initialize_node(init_directory: str=DEFAULT_INIT_DIR) -> None:
    """Initialize new node in .node directory
    Create the private key file"""
    if os.path.exists(init_directory):
        raise FileExistsError

    os.mkdir(init_directory)
    private_key = crypto_util.generate_private_key()
    write_private_key_to_disk(private_key, init_directory)


def write_private_key_to_disk(
    key: crypto_util.rsa.RSAPrivateKey, init_directory: str,
) -> None:
    """Write Private Key (and public key attached) to file"""
    if os.path.exists(os.path.join(init_directory, "private_key.pem")):
        raise FileExistsError

    with open(
        os.path.join(init_directory, "private_key.pem"),
        "wb",
    ) as keyfile:
        keyfile.write(crypto_util.dump_private_key(key))
        keyfile.close()


def load_private_key_from_disk(
    init_directory: str,
) -> crypto_util.rsa.RSAPrivateKey:
    """Load Private Key (and public key) from file"""
    with open(
        os.path.join(init_directory, "private_key.pem"),
        "rb",
    ) as keyfile:
        return crypto_util.load_private_key(keyfile.read())
