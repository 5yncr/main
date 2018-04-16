import asyncio
import os
import shutil
from random import shuffle
from typing import AsyncIterator
from typing import Awaitable  # noqa
from typing import cast
from typing import Dict  # noqa
from typing import List
from typing import Optional  # noqa
from typing import Set
from typing import Tuple
from typing import TypeVar

from cachetools import TTLCache  # type: ignore

from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import DEFAULT_FILE_METADATA_LOCATION
from syncr_backend.constants import MAX_CHUNKS_PER_PEER
from syncr_backend.constants import MAX_CONCURRENT_CHUNK_DOWNLOADS
from syncr_backend.constants import MAX_CONCURRENT_FILE_DOWNLOADS
from syncr_backend.constants import TRACKER_DROP_AVAILABILITY_TTL
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
from syncr_backend.util import async_util
from syncr_backend.util import crypto_util
from syncr_backend.util import fileio_util
from syncr_backend.util.crypto_util import VerificationException
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


async def sync_drop(drop_id: bytes, save_dir: str) -> bool:
    """
    Syncs a drop id from remote peers

    :param drop_id: id of drop to sync
    :param save_dir: directory to save drop
    """
    drop_peers = await get_drop_peers(drop_id)
    await start_drop_from_id(drop_id, save_dir)
    drop_metadata = await get_drop_metadata(drop_id, drop_peers, save_dir)

    file_results = await async_util.limit_gather(
        fs=[
            sync_and_finish_file(
                drop_id=drop_id,
                file_name=file_name,
                file_id=file_id,
                # call rotate(drop_peers) so each file starts with a new peer
                peers=rotate(drop_peers),
                save_dir=save_dir,
            ) for file_name, file_id in drop_metadata.files.items()
        ],
        n=MAX_CONCURRENT_FILE_DOWNLOADS,
        task_timeout=1,
    )

    return all(file_results)


T = TypeVar('T')


def rotate(l: List[T]) -> List[T]:
    """Puts the first element at the back and return the list
    :param l: a list
    :return: that list, with the first element at the back
    """
    if len(l) <= 1:
        return l
    l.append(l.pop(0))
    return l


async def sync_and_finish_file(
    drop_id: bytes, file_name: str, file_id: bytes,
    peers: List[Tuple[str, int]], save_dir: str,
) -> bool:
    remaining_chunks = await sync_file_contents(
        drop_id=drop_id,
        file_name=file_name,
        file_id=file_id,
        peers=peers,
        save_dir=save_dir,
    )
    if not remaining_chunks:
        full_file_name = os.path.join(save_dir, file_name)
        fileio_util.mark_file_complete(full_file_name)
        return True
    return False


class PermissionError(Exception):
    pass


async def update_drop(
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
    peers = await get_drop_peers(drop_id)
    old_drop_metadata = await get_drop_metadata(drop_id, peers)
    priv_key = await node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())

    if old_drop_metadata.owner != node_id:
        raise PermissionError("You are not the owner of this drop")

    drop_directory = await get_drop_location(drop_id)
    (new_drop_m, new_files_m) = await drop_init.make_drop_metadata(
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

    await new_drop_m.write_file(
        is_latest=True,
        metadata_location=os.path.join(
            drop_directory, DEFAULT_DROP_METADATA_LOCATION,
        ),
    )
    for f_m in new_files_m.values():
        await f_m.write_file(
            os.path.join(drop_directory, DEFAULT_FILE_METADATA_LOCATION),
        )


async def start_drop_from_id(drop_id: bytes, save_dir: str) -> None:
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
    await save_drop_location(drop_id, save_dir)


async def get_drop_metadata(
    drop_id: bytes, peers: List[Tuple[str, int]], save_dir: Optional[str]=None,
    version: Optional[DropVersion]=None,
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
        save_dir = await get_drop_location(drop_id)
    logger.debug("save_dir is %s", save_dir)
    metadata_dir = os.path.join(save_dir, DEFAULT_DROP_METADATA_LOCATION)
    metadata = await DropMetadata.read_file(
        id=drop_id, metadata_location=metadata_dir,
    )

    if metadata is None:
        logger.debug("drop metadata not on disk, getting from network")
        args = {
            'drop_id': drop_id,
            'drop_version': version,
        }
        metadata = await send_requests.do_request(
            request_fun=send_requests.send_drop_metadata_request,
            peers=peers,
            fun_args=args,
        )
        # mypy can't figure out that this won't be None
        metadata = cast(DropMetadata, metadata)

        await metadata.write_file(
            is_latest=True, metadata_location=metadata_dir,
        )

    return metadata


async def verify_version(
    drop_metadata: DropMetadata,
    peers: Optional[List[Tuple[str, int]]]=None,
) -> None:
    """Verify the DropMetadata version recursively

    If this version and all prior versions leading up to it are legitimate
    returns none, otherwise throws an exception
    """
    if len(drop_metadata.previous_versions) == 0:
        await drop_metadata.verify_header()
        return
    elif len(drop_metadata.previous_versions) == 1:
        version = drop_metadata.previous_versions[0]
        if peers is None:
            peers = await get_drop_peers(drop_metadata.id)
        dmd = await get_drop_metadata(drop_metadata.id, peers, version=version)
        verify_version(dmd, peers)

        if drop_metadata.signed_by == dmd.owner:
            logger.debug(
                "Beginning ownership change verification for drop: %s",
                drop_metadata.id,
            )
            await drop_metadata.verify_header()
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
            await drop_metadata.verify_header()
    else:
        #  Ownership changes are not allowed in merges and must be signed by
        #  primary owner
        primary_owner = drop_metadata.owner
        if primary_owner != drop_metadata.signed_by:
            raise VerificationException()
        for version in drop_metadata.previous_versions:
            if peers is None:
                peers = await get_drop_peers(drop_metadata.id)
            dmd = await get_drop_metadata(
                drop_metadata.id, peers, version=version,
            )
            await verify_version(dmd, peers)
            if primary_owner != dmd.owner:
                raise VerificationException()


async def simple_get_drop_metadata(drop_id: bytes) -> DropMetadata:
    """
    Get drop_metadata object from just drop_id
    :param drop_id:
    :return: A drop_metadata object
    """
    peers = await get_drop_peers(drop_id)
    drop_metadata = await get_drop_metadata(drop_id, peers)

    return drop_metadata


async def get_owned_drops_metadata() -> List[DropMetadata]:
    """
    Get list of metadata objects for owned drops (primary and secondary)
    :return: list of metadata objects this node owns
    """
    drops = list_drops()

    # Get current nodes id
    priv_key = await node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())

    owned_drops = []

    for drop_id in drops:
        # Get drop_metadata object for drop
        md = await simple_get_drop_metadata(drop_id)
        if md.owner == node_id:
            owned_drops.append(md)
        else:
            for owner in md.other_owners:
                if owner == node_id:
                    owned_drops.append(md)

    return owned_drops


async def get_subscribed_drops_metadata() -> List[DropMetadata]:
    """
    Get list of metadata objects for subscribed drops
    :return: list of metadata objects this node is subscribed to
    """
    drops = list_drops()

    # Get current nodes id
    priv_key = await node_init.load_private_key_from_disk()
    node_id = crypto_util.node_id_from_public_key(priv_key.public_key())

    subscribed_drops = []

    # Subscribed drops are those on the disk that this node does not own
    for drop_id in drops:
        # Get drop_metadata object for drop
        md = await simple_get_drop_metadata(drop_id)
        if md.owner != node_id and node_id not in md.other_owners:
            subscribed_drops.append(md)

    return subscribed_drops


async def get_file_metadata(
    drop_id: bytes, file_id: bytes, save_dir: str, file_name: str,
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
    metadata = await FileMetadata.read_file(
        file_id=file_id, metadata_location=metadata_dir, file_name=file_name,
    )
    if metadata is None:
        logger.debug("file metadata not on disk, getting from network")
        metadata = await send_requests.do_request(
            request_fun=send_requests.send_file_metadata_request,
            peers=peers,
            fun_args={'drop_id': drop_id, 'file_id': file_id},
        )

        if metadata is None:
            raise Exception

        await metadata.write_file(metadata_dir)

    return metadata


async def sync_file_contents(
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
    logger.info("syncing contents of file %s", file_name)
    logger.debug("save dir is %s", save_dir)
    file_metadata = await get_file_metadata(
        drop_id, file_id, save_dir, file_name, peers,
    )
    file_metadata.file_name = file_name
    full_path = os.path.join(save_dir, file_name)
    needed_chunks = None  # type: Optional[Set[int]]
    try:
        needed_chunks = await file_metadata.needed_chunks
    except FileNotFoundError:
        needed_chunks = None

    if not needed_chunks and needed_chunks is not None:
        if not await file_metadata.downloaded_chunks:
            # if it's an empty file, there are no needed chunks, but we still
            #  need to create the file
            await fileio_util.create_file(full_path, file_metadata.file_length)
        return needed_chunks

    await fileio_util.create_file(full_path, file_metadata.file_length)

    if needed_chunks is None:
        needed_chunks = await file_metadata.needed_chunks

    process_queue = asyncio.Queue()  # type: asyncio.Queue[Awaitable[Optional[int]]] # noqa
    result_queue = asyncio.Queue()  # type: asyncio.Queue[Optional[int]]

    processor = asyncio.ensure_future(
        async_util.process_queue_with_limit(
            process_queue, MAX_CONCURRENT_CHUNK_DOWNLOADS, result_queue, 1,
        ),
    )

    while needed_chunks:
        added = 0
        async for (ip, port), chunks_to_download in peers_and_chunks(
            peers, needed_chunks, drop_id, file_id, MAX_CHUNKS_PER_PEER,
        ):
            for cid in chunks_to_download:
                await process_queue.put(
                    download_chunk_form_peer(
                        ip=ip,
                        port=port,
                        drop_id=drop_id,
                        file_id=file_id,
                        file_index=cid,
                        file_metadata=file_metadata,
                        full_path=full_path,
                    ),
                )
                added += 1

        await process_queue.join()
        while not result_queue.empty():
            result = await result_queue.get()
            if result is not None:
                needed_chunks.remove(result)
            result_queue.task_done()
        if not added:
            break

    processor.cancel()
    return needed_chunks


async def peers_and_chunks(
    peers: List[Tuple[str, int]], needed_chunks: Set[int],
    drop_id: bytes, file_id: bytes, chunks_per_peer: int,
) -> AsyncIterator[Tuple[Tuple[str, int], Set[int]]]:
    """
    For each peer, figure out what chunks it has, then yield the first
    chunks_per_peer chunks that haven't been reserved for another peer

    :param peers: Peer list
    :param needed_chunks: Needed chunks
    :param drop_id: Drop ID
    :param file_id: File ID
    :param chunks_per_peer: How many chunks each peer gets assigned
    :return: Async Iterator over peers and sets of chunk indexes
    """
    needed_chunks = needed_chunks.copy()
    for ip, port in peers:
        avail_chunks = await get_chunk_list(ip, port, drop_id, file_id)
        can_get_from_peer = avail_chunks & needed_chunks
        chunks_for_peer = set(list(can_get_from_peer)[:chunks_per_peer])
        needed_chunks -= chunks_for_peer
        yield ((ip, port), chunks_for_peer)
        if not needed_chunks:
            break


@async_util.async_cache(
    maxsize=1024, cache_obj=TTLCache, ttl=TRACKER_DROP_AVAILABILITY_TTL,
)
async def get_chunk_list(
    ip: str, port: int, drop_id: bytes, file_id: bytes,
) -> Set[int]:
    return set(await send_requests.send_chunk_list_request(
        ip=ip,
        port=port,
        drop_id=drop_id,
        file_id=file_id,
    ))


async def download_chunk_form_peer(
    ip: str, port: int, drop_id: bytes, file_id: bytes, file_index: int,
    file_metadata: FileMetadata, full_path: str,
) -> Optional[int]:
    """Download a chunk from a peer, and if it succeeds mark that chunk done
    in the File Metadata

    :param ip: Peer ip
    :param port: Peer port
    :param drop_id: Drop ID
    :param file_id: File ID
    :param file_index: Chunk index
    :param file_metadata: The file metadata
    :param full_path: The path of the file
    :return: The chunk id if success, otherwise None
    """
    chunk = await send_requests.send_chunk_request(
        ip=ip,
        port=port,
        drop_id=drop_id,
        file_id=file_id,
        file_index=file_index,
    )
    try:
        await fileio_util.write_chunk(
            filepath=full_path,
            position=file_index,
            contents=chunk,
            chunk_hash=file_metadata.hashes[file_index],
        )
        await file_metadata.finish_chunk(file_index)
        return file_index
    except crypto_util.VerificationException as e:
        logger.warning(
            "verification exception (%s) from peer %s, skipping",
            e, ip,
        )
        return None


class PeerStoreError(Exception):
    pass


async def get_drop_peers(drop_id: bytes) -> List[Tuple[str, int]]:
    """
    Gets the peers that have a drop. Also shuffles the list
    :param drop_id: id of drop
    :return: A list of peers in format (ip, port)
    """
    priv_key = await node_init.load_private_key_from_disk()
    node_id = await crypto_util.node_id_from_public_key(priv_key.public_key())
    drop_peer_store_instance = await drop_peer_store.get_drop_peer_store(
        node_id,
    )
    success, drop_peers = await drop_peer_store_instance.request_peers(drop_id)
    if not success:
        raise PeerStoreError("Could not connect to peers")

    peers = [(ip, int(port)) for peer_name, ip, port in drop_peers]

    shuffle(peers)

    return peers
