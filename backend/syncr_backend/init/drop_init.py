import os

from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import DEFAULT_FILE_METADATA_LOCATION
from syncr_backend.constants import DEFAULT_METADATA_LOOKUP_LOCATION
from syncr_backend.init import node_init
from syncr_backend.metadata import drop_metadata
from syncr_backend.util import crypto_util


def initialize_drop(directory: str) -> None:
    """Initialize a drop from a directory. Generates the necesssary drop and
    file metadata files and writes the drop location to the central config dif

    :param directory: The directory to initialize a drop from
    """
    priv_key = node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())
    (drop_m, files_m) = drop_metadata.make_drop_metadata(
        path=directory,
        drop_name=os.path.basename(directory),
        owner=node_id,
    )
    drop_m.write_file(
        is_latest=True,
        metadata_location=os.path.join(
            directory, DEFAULT_DROP_METADATA_LOCATION,
        ),
    )
    for f_m in files_m.values():
        f_m.write_file(
            os.path.join(directory, DEFAULT_FILE_METADATA_LOCATION),
        )
    save_drop_location(drop_m.id, directory)


def save_drop_location(drop_id: bytes, location: str) -> None:
    """Save a drops location in the central data dir

    :param drop_id: The unencoded drop id
    :param location: Where the drop is located on disk
    """
    save_path = _get_save_path()

    encoded_drop_id = crypto_util.b64encode(drop_id).decode('utf-8')

    with open(os.path.join(save_path, encoded_drop_id), 'w') as f:
        f.write(location)


def get_drop_location(drop_id: bytes) -> str:
    """Get a drops location on disk, from the drop id

    :param drop_id: The unencoded drop id
    :return: The directory the drop is in
    """
    save_path = _get_save_path()

    encoded_drop_id = crypto_util.b64encode(drop_id).decode('utf-8')

    with open(os.path.join(save_path, encoded_drop_id), 'r') as f:
        return f.read()


def _get_save_path() -> str:
    node_info_path = node_init.get_full_init_directory()
    save_path = os.path.join(node_info_path, DEFAULT_METADATA_LOOKUP_LOCATION)
    return save_path
