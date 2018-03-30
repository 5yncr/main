import os
import shutil
from typing import List
from typing import Optional  # noqa
from typing import Set
from typing import Tuple

from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import DEFAULT_FILE_METADATA_LOCATION
from syncr_backend.external_interface import drop_peer_store
from syncr_backend.init import drop_init
from syncr_backend.init import node_init
from syncr_backend.metadata import drop_metadata
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import get_drop_location
from syncr_backend.metadata.drop_metadata import save_drop_location
from syncr_backend.metadata.file_metadata import FileMetadata
from syncr_backend.network import send_requests
from syncr_backend.util import crypto_util
from syncr_backend.util import fileio_util
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


def sync_drop(drop_id: bytes, save_dir: str):
    """
    Syncs a drop id from remote peers

    :param drop_id: id of drop to sync
    :param save_dir: directory to save drop
    """
    drop_peers = get_drop_peers(drop_id)

    add_drop_from_id(drop_id, save_dir)
    drop_metadata = get_drop_metadata(drop_id, drop_peers, save_dir)
    for file_name, file_id in drop_metadata.files.items():
        remaining_chunks = sync_drop_contents(
            drop_id=drop_id,
            file_id=file_id,
            peers=drop_peers,
            save_dir=save_dir,
        )
        if not remaining_chunks:
            fileio_util.mark_file_complete(file_name)


class PermissionError(Exception):
    pass


def update_drop(drop_id: bytes) -> None:
    """
    Update a drop from a directory.

    :param drop_id: The drop_id to update
    :param peers: list of peers to get drop metadata from if missing

    """
    peers = get_drop_peers(drop_id)

    old_drop_metadata = get_drop_metadata(drop_id, peers)
    priv_key = node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())

    if old_drop_metadata.owner != node_id:
        raise PermissionError("You are not the owner of this drop")

    drop_directory = get_drop_location(drop_id)
    (new_drop_m, new_files_m) = drop_init.make_drop_metadata(
        path=drop_directory,
        drop_name=old_drop_metadata.name,
        owner=old_drop_metadata.owner,
    )
    new_drop_m.other_owners = old_drop_metadata.other_owners
    new_drop_m.version = drop_metadata.DropVersion(
        old_drop_metadata.version.version + 1,
        crypto_util.random_int(),
    )
    # deletes the existing metadata files
    shutil.rmtree(
        os.path.join(
            drop_directory, DEFAULT_DROP_METADATA_LOCATION,
        ),
    )

    new_drop_m.write_file(
        is_latest=True,
        metadata_location=os.path.join(
            drop_directory, DEFAULT_DROP_METADATA_LOCATION,
        ),
    )
    for f_m in new_files_m.values():
        f_m.write_file(
            os.path.join(drop_directory, DEFAULT_FILE_METADATA_LOCATION),
        )


def add_drop_from_id(drop_id: bytes, save_dir: str) -> None:
    """Given a drop_id and save directory, sets up the directory for syncing
    and adds the info to the global dir

    Should be followed by calls to `get_drop_metadata`, `get_file_metadata` for
    each file, and `sync_drop_contents`

    :param drop_id: The drop id to add
    :param save_dir: where to download the drop to
    """

    logger.info(
        "Adding drop from id %s to %s", crypto_util.b64encode(
            drop_id,
        ), save_dir,
    )
    os.makedirs(
        os.path.join(save_dir, DEFAULT_DROP_METADATA_LOCATION), exist_ok=True,
    )
    os.makedirs(
        os.path.join(save_dir, DEFAULT_FILE_METADATA_LOCATION), exist_ok=True,
    )
    save_drop_location(drop_id, save_dir)


def get_drop_metadata(
    drop_id: bytes, peers: List[Tuple[str, int]], save_dir: Optional[str]=None,
) -> DropMetadata:
    """Get drop metadata, given a drop id and save dir.  If the drop metadata
    is not on disk already, attempt to download from peers.

    :param drop_id: the drop id
    :param save_dir: where the drop is saved
    :param peers: where to look on the network for data
    :return: A drop metadata object
    """
    logger.info("getting drop metadata for %s", crypto_util.b64encode(drop_id))
    metadata = None
    if save_dir is not None:
        metadata_dir = os.path.join(save_dir, DEFAULT_DROP_METADATA_LOCATION)
        metadata = DropMetadata.read_file(drop_id, metadata_dir)

    if metadata is None:
        logger.debug("drop metadata not on disk, getting from network")
        metadata = send_requests.do_request(
            request_fun=send_requests.send_drop_metadata_request,
            peers=peers,
            fun_args={'drop_id': drop_id},
        )

        metadata.write_file(is_latest=True, metadata_location=metadata_dir)

    return metadata


def get_file_metadata(
    drop_id: bytes, file_id: bytes, save_dir: str,
    peers: List[Tuple[str, int]],
) -> FileMetadata:
    """Get file metadata, given a file id, drop id and save dir.  If the file
    metadata is not on disk already, attempt to download from peers.

    :param drop_id: the drop id
    :param file_id: the file id
    :param save_dir: where the drop is saved
    :param peers: where to look on the network for data
    :return: A file metadata object
    """
    logger.info("getting file metadata for %s", crypto_util.b64encode(file_id))
    metadata_dir = os.path.join(save_dir, DEFAULT_FILE_METADATA_LOCATION)
    metadata = FileMetadata.read_file(file_id, metadata_dir)
    if metadata is None:
        logger.debug("file metadata not on disk, getting from network")
        metadata = send_requests.do_request(
            request_fun=send_requests.send_file_metadata_request,
            peers=peers,
            fun_args={'drop_id': drop_id, 'file_id': file_id},
        )

        metadata.write_file(metadata_dir)

    return metadata


def sync_drop_contents(
    drop_id: bytes, file_id: bytes,
    peers: List[Tuple[str, int]], save_dir: str,
) -> Set[int]:
    """Download as much of a file as possible

    :param drop_id: the drop the file is in
    :param file_id: the file to download
    :param save_dir: where the drop is saved
    :param peers: where to look for chunks
    :return: A set of chunk ids NOT downloaded
    """
    logger.info("syncing contents of file %s", crypto_util.b64encode(file_id))
    file_metadata = get_file_metadata(drop_id, file_id, save_dir, peers)
    drop_metadata = get_drop_metadata(drop_id, peers)
    file_name = drop_metadata.get_file_name_from_id(file_metadata.file_id)
    full_path = os.path.join(save_dir, file_name)

    fileio_util.create_file(full_path, file_metadata.file_length)

    for ip, port in peers:
        logger.debug("trying peer %s", ip)
        needed_chunks = file_metadata.needed_chunks
        avail_chunks = send_requests.send_chunk_list_request(
            ip=ip,
            port=port,
            drop_id=drop_id,
            file_id=file_id,
        )
        avail_set = set(avail_chunks)
        can_get_from_peer = avail_set & needed_chunks
        if not can_get_from_peer:
            logger.debug("no chunks available, skipping")
            continue
        for cid in can_get_from_peer:
            logger.debug("trying to download chunk %s from %s", cid, ip)
            chunk = send_requests.send_chunk_request(
                ip=ip,
                port=port,
                drop_id=drop_id,
                file_id=file_id,
                file_index=cid,
            )
            try:
                fileio_util.write_chunk(
                    filepath=full_path,
                    position=cid,
                    contents=chunk,
                    chunk_hash=file_metadata.hashes[cid],
                )
                file_metadata.finish_chunk(cid)
                needed_chunks -= {cid}
            except crypto_util.VerificationException as e:
                logger.warning(
                    "verification exception (%s) from peer %s, skipping",
                    e, ip,
                )
                break

    return needed_chunks


class PeerStoreError(Exception):
    pass


def get_drop_peers(drop_id: bytes) -> List[Tuple[str, int]]:
    """
    Gets the peers that have a drop
    :param drop_id: id of drop
    """
    priv_key = node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())
    drop_peer_store_instance = drop_peer_store.get_drop_peer_store(node_id)
    success, drop_peers = drop_peer_store_instance.request_peers(drop_id)
    if not success:
        raise PeerStoreError("Could not connect to peers")

    return [(ip, int(port)) for peer_name, ip, port in drop_peers]
