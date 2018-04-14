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
from syncr_backend.metadata.drop_metadata import DropVersion
from syncr_backend.metadata.drop_metadata import get_drop_location
from syncr_backend.metadata.drop_metadata import list_drops
from syncr_backend.metadata.drop_metadata import save_drop_location
from syncr_backend.metadata.file_metadata import FileMetadata
from syncr_backend.network import send_requests
from syncr_backend.util import crypto_util
from syncr_backend.util import fileio_util
from syncr_backend.util.crypto_util import VerificationException
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


def sync_drop(drop_id: bytes, save_dir: str) -> bool:
    """
    Syncs a drop id from remote peers

    :param drop_id: id of drop to sync
    :param save_dir: directory to save drop
    """
    drop_peers = get_drop_peers(drop_id)
    start_drop_from_id(drop_id, save_dir)
    drop_metadata = get_drop_metadata(drop_id, drop_peers, save_dir)
    all_done = True
    for file_name, file_id in drop_metadata.files.items():
        logger.debug(
            "Downloading file %s with id %s", file_name,
            crypto_util.b64encode(file_id),
        )
        remaining_chunks = sync_file_contents(
            drop_id=drop_id,
            file_name=file_name,
            file_id=file_id,
            peers=drop_peers,
            save_dir=save_dir,
        )
        if not remaining_chunks:
            full_file_name = os.path.join(save_dir, file_name)
            fileio_util.mark_file_complete(full_file_name)
        else:
            all_done = False

    return all_done


class PermissionError(Exception):
    pass


def update_drop(
        drop_id: bytes,
        add_secondary_owner: bytes=None,
        remove_secondary_owner: bytes=None,
        add_file: bytes=None,
        remove_file: bytes=None,
        file_name: str=None,
) -> None:
    """
    Update a drop from a directory.

    :param drop_id: The drop_id to update
    :param add_secondary_owner: new secondary owner for a drop
    :param remove_secondary_owner: secondary owner to remove from a drop
    :param add_file: new file to be added to a drop
    :param remove_file: file to be removed from a drop
    :param file_name: name of file to be added/removed.

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

    # Updating secondary owners
    if add_secondary_owner is not None \
            and add_secondary_owner not in old_drop_metadata.other_owners:
        old_drop_metadata.other_owners.update({add_secondary_owner: 1})
    if remove_secondary_owner is not None \
            and remove_secondary_owner in old_drop_metadata.other_owners:
        old_drop_metadata.other_owners.pop(remove_secondary_owner)

    new_drop_m.other_owners = old_drop_metadata.other_owners

    # Updating current files.
    if add_file is not None \
            and add_file not in old_drop_metadata.files \
            and file_name is not None:
        old_drop_metadata.files.update({file_name: add_file})
    if remove_file is not None \
            and remove_file in old_drop_metadata.files \
            and file_name is not None:
        old_drop_metadata.files.pop(file_name)
    new_drop_m.files = old_drop_metadata.files

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


def start_drop_from_id(drop_id: bytes, save_dir: str) -> None:
    """Given a drop_id and save directory, sets up the directory for syncing
    and adds the info to the global dir

    Should be followed by calls to `get_drop_metadata`, `get_file_metadata` for
    each file, and `sync_file_contents`

    :param drop_id: The drop id to add
    :param save_dir: where to download the drop to
    """

    logger.info(
        "Adding drop from id %s to %s", crypto_util.b64encode(drop_id),
        save_dir,
    )
    os.makedirs(
        os.path.join(save_dir, DEFAULT_DROP_METADATA_LOCATION), exist_ok=True,
    )
    os.makedirs(
        os.path.join(save_dir, DEFAULT_FILE_METADATA_LOCATION), exist_ok=True,
    )
    save_drop_location(drop_id, save_dir)


def get_drop_metadata(
    drop_id: bytes, peers: List[Tuple[str, int]], save_dir:
    Optional[str]=None, version: Optional[DropVersion]=None,
) -> DropMetadata:
    """Get drop metadata, given a drop id and save dir.  If the drop metadata
    is not on disk already, attempt to download from peers.

    :param drop_id: the drop id
    :param peers: where to look on the network for data
    :param save_dir: where the drop is saved
    :return: A drop metadata object
    """
    logger.info("getting drop metadata for %s", crypto_util.b64encode(drop_id))
    if save_dir is None:
        logger.debug("save_dir not set, trying to look it up")
        save_dir = get_drop_location(drop_id)
    logger.debug("save_dir is %s", save_dir)
    metadata_dir = os.path.join(save_dir, DEFAULT_DROP_METADATA_LOCATION)
    metadata = DropMetadata.read_file(drop_id, metadata_dir)

    if metadata is None:
        logger.debug("drop metadata not on disk, getting from network")
        args = {
            'drop_id': drop_id,
            'drop_version': version,
        }
        metadata = send_requests.do_request(
            request_fun=send_requests.send_drop_metadata_request,
            peers=peers,
            fun_args=args,
        )

        metadata.write_file(is_latest=True, metadata_location=metadata_dir)

    return metadata


def verify_version(
    drop_metadata: DropMetadata,
    peers: Optional[List[Tuple[str, int]]]=None,
) -> None:
    """Verify the DropMetadata version recursively

    If this version and all prior versions leading up to it are legitimate
    returns none, otherwise throws an exception
    """
    if len(drop_metadata.previous_versions) == 0:
        drop_metadata.verify_header()
        return
    elif len(drop_metadata.previous_versions) == 1:
        version = drop_metadata.previous_versions[0]
        if peers is None:
            peers = get_drop_peers(drop_metadata.id)
        dmd = get_drop_metadata(drop_metadata.id, peers, version=version)
        verify_version(dmd, peers)

        if drop_metadata.signed_by == dmd.owner:
            logger.debug(
                "Beginning ownership change verification for drop: %s",
                drop_metadata.id,
            )
            drop_metadata.verify_header()
            logger.debug(
                "Ownership change verified for drop: %s",
                drop_metadata.id,
            )
        # TODO change in case of other owners becoming a list
        elif drop_metadata.signed_by not in drop_metadata.other_owners.keys() \
                or drop_metadata.signed_by != drop_metadata.owner:
            logger.debug(
                "%s signed as not owner on drop %s",
                drop_metadata.signed_by,
                drop_metadata.id,
            )
            raise VerificationException()
        else:
            drop_metadata.verify_header()
    else:
        #  Ownership changes are not allowed in merges and must be signed by
        #  primary owner
        primary_owner = drop_metadata.owner
        if primary_owner != drop_metadata.signed_by:
            raise VerificationException()
        for version in drop_metadata.previous_versions:
            if peers is None:
                peers = get_drop_peers(drop_metadata.id)
            dmd = get_drop_metadata(drop_metadata.id, peers, version=version)
            verify_version(dmd, peers)
            if primary_owner != dmd.owner:
                raise VerificationException()


def simple_get_drop_metadata(drop_id: bytes) -> DropMetadata:
    """
    Get drop_metadata object from just drop_id
    :param drop_id:
    :return: A drop_metadata object
    """
    peers = get_drop_peers(drop_id)
    drop_metadata = get_drop_metadata(drop_id, peers)

    return drop_metadata


def get_owned_drops_metadata() -> List[DropMetadata]:
    """
    Get list of metadata objects for owned drops (primary and secondary)
    :return: list of metadata objects this node owns
    """
    drops = list_drops()

    # Get current nodes id
    priv_key = node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())

    owned_drops = []

    for drop_id in drops:
        # Get drop_metadata object for drop
        md = simple_get_drop_metadata(drop_id)
        if md.owner == node_id:
            owned_drops.append(md)
        else:
            for owner in md.other_owners:
                if owner == node_id:
                    owned_drops.append(md)

    return owned_drops


def get_subscribed_drops_metadata() -> List[DropMetadata]:
    """
    Get list of metadata objects for subscribed drops
    :return: list of metadata objects this node is subscribed to
    """
    drops = list_drops()

    # Get current nodes id
    priv_key = node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())

    subscribed_drops = []

    # Subscribed drops are those on the disk that this node does not own
    for drop_id in drops:
        # Get drop_metadata object for drop
        md = simple_get_drop_metadata(drop_id)
        if md.owner != node_id and node_id not in md.other_owners:
            subscribed_drops.append(md)

    return subscribed_drops


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


def sync_file_contents(
    drop_id: bytes, file_id: bytes, file_name: str,
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
    logger.debug("save dir is %s", save_dir)
    file_metadata = get_file_metadata(drop_id, file_id, save_dir, peers)
    file_metadata.file_name = file_name
    full_path = os.path.join(save_dir, file_name)
    try:
        needed_chunks = file_metadata.needed_chunks  # type: Optional[Set[int]]
    except FileNotFoundError:
        needed_chunks = None

    if not needed_chunks and needed_chunks is not None:
        if not file_metadata.downloaded_chunks:
            # if it's an empty file, there are no needed chunks, but we still
            #  need to create the file
            fileio_util.create_file(full_path, file_metadata.file_length)
        return needed_chunks

    fileio_util.create_file(full_path, file_metadata.file_length)

    if needed_chunks is None:
        needed_chunks = file_metadata.needed_chunks

    for ip, port in peers:
        logger.debug("trying peer %s", ip)
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
