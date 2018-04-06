"""Functions for initializing or adding a new drop"""
import os
from typing import Dict
from typing import List
from typing import Optional  # noqa
from typing import Tuple

from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import DEFAULT_FILE_METADATA_LOCATION
from syncr_backend.init import node_init
from syncr_backend.metadata import drop_metadata
from syncr_backend.metadata import file_metadata
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import save_drop_location
from syncr_backend.metadata.file_metadata import FileMetadata
from syncr_backend.util import crypto_util
from syncr_backend.util import fileio_util
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


def initialize_drop(directory: str) -> bytes:
    """Initialize a drop from a directory. Generates the necesssary drop and
    file metadata files and writes the drop location to the central config dif

    :param directory: The directory to initialize a drop from
    :return: The b64 encoded id of the created drop
    """
    logger.info("initializing drop in dir %s", directory)
    priv_key = node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())
    (drop_m, files_m) = make_drop_metadata(
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
    logger.info("drop initialized with %s files", len(files_m))

    return crypto_util.b64encode(drop_m.id)


def make_drop_metadata(
    path: str,
    drop_name: str,
    owner: bytes,
    other_owners: Dict[bytes, int]={},
    ignore: List[str]=[],
) -> Tuple[DropMetadata, Dict[str, FileMetadata]]:
    """Makes drop metadata and file metadatas from a directory

    :param path: The directory to make metadata from
    :param name: The name of the drop to create
    :param drop_id: The drop id of the drop metadata, must match the owner
    :param owner: The owner, must match the drop id
    :param other_owners: Other owners, may be empty
    :return: A tuple of the drop metadata, and a dict from file names to file
    metadata
    """
    logger.info("creating drop metadata for drop name %s", drop_name)
    drop_id = drop_metadata.gen_drop_id(owner)
    files = {}
    for (dirpath, filename) in fileio_util.walk_with_ignore(path, ignore):
        full_name = os.path.join(dirpath, filename)
        files[full_name] = file_metadata.make_file_metadata(full_name, drop_id)

    file_hashes = {
        os.path.relpath(name, path): m.file_id for (name, m) in files.items()
    }
    dm = DropMetadata(
        drop_id=drop_id,
        name=drop_name,
        version=drop_metadata.DropVersion(1, crypto_util.random_int()),
        previous_versions=[],
        primary_owner=owner,
        other_owners=other_owners,
        signed_by=owner,
        files=file_hashes,
    )

    logger.debug("metadata generated with %s files", len(files))
    return (dm, files)
