"The dorp metadata object and related functions"""
import logging
import os
import shutil
from typing import Any
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import aiofiles  # type: ignore
import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_METADATA_LOOKUP_LOCATION
from syncr_backend.constants import DEFAULT_PUB_KEY_LOOKUP_LOCATION
from syncr_backend.external_interface.public_key_store import \
    get_public_key_store
from syncr_backend.init import node_init
from syncr_backend.init.node_init import get_full_init_directory
from syncr_backend.init.node_init import load_private_key_from_disk
from syncr_backend.util import crypto_util
from syncr_backend.util.async_util import async_cache
from syncr_backend.util.crypto_util import load_public_key
from syncr_backend.util.crypto_util import node_id_from_private_key
from syncr_backend.util.crypto_util import VerificationException
from syncr_backend.util.log_util import get_logger


LATEST = "LATEST"

logger = get_logger(__name__)


class DropVersion(object):
    """A drop version"""

    def __init__(self, version: int, nonce: int) -> None:
        self.version = version
        self.nonce = nonce

    def __iter__(self) -> Iterator[Tuple[str, Union['DropVersion', int]]]:
        """Used for calling dict() on this object, so it becomes
        {'version': version, 'nonce': nonce}
        """
        yield 'version', self.version
        yield 'nonce', self.nonce

    def __str__(self) -> str:
        return "%s_%s" % (self.version, self.nonce)


class DropMetadata(object):
    """Representation of a drop's metadata file"""

    def __init__(
        self, drop_id: bytes, name: str, version: DropVersion,
        previous_versions: List[DropVersion], primary_owner: bytes,
        other_owners: Dict[bytes, int], signed_by: bytes,
        files: Dict[str, bytes],
        files_hash: Optional[bytes]=None, sig: Optional[bytes]=None,
        protocol_version: int=1,
    ) -> None:
        self.id = drop_id
        self.name = name
        self.version = version
        self.previous_versions = previous_versions
        self.owner = primary_owner
        self.other_owners = other_owners
        self.signed_by = signed_by
        self.files = files
        self.sig = sig
        self._protocol_version = protocol_version
        self._files_hash = files_hash
        self._log = None  # type: Optional[logging.Logger]

    @property
    def log(self) -> logging.Logger:
        """A logger for this object"""
        if self._log is None:
            self._log = get_logger(
                '.'.join([
                    __name__, self.__class__.__name__,
                    crypto_util.b64encode(self.id).decode('utf-8'),
                ]),
            )
        return self._log

    @property
    async def files_hash(self) -> bytes:
        """Generate the hash of the files dictionary

        :return: The hash of the bencoded files dict
        """
        if self._files_hash is not None:
            return self._files_hash
        else:
            h = await self._gen_files_hash()
            self._files_hash = h
            return h

    async def _gen_files_hash(self) -> bytes:
        return await crypto_util.hash_dict(self.files)

    async def verify_files_hash(self) -> None:
        """Verify the file hash in this object

        Returns None if the hash is OK, throwns a VerificationException if the
        hash is not good or has not been set
        """
        if self._files_hash is None:
            self.log.error("no files hash found when verifying")
            raise VerificationException()
        given = self._files_hash
        expected = await self._gen_files_hash()
        if given != expected:
            self.log.error("files verification failed!")
            raise VerificationException()

    @property
    async def unsigned_header(self) -> Dict[str, Any]:
        """Get the unsigned version of the header
        The signature is set to b"", and the files list is {}

        :return: A dict that is the drop metadata header, without a signature
        """
        h = {
            "protocol_version": self._protocol_version,
            "drop_id": self.id,
            "name": self.name,
            "version": self.version.version,
            "version_nonce": self.version.nonce,
            "previous_versions": [dict(v) for v in self.previous_versions],
            "primary_owner": self.owner,
            "other_owners": self.other_owners,
            "header_signature": b"",
            "signed_by": self.signed_by,
            "files_hash": await self.files_hash,
            "files": {},
        }
        return h

    @property
    async def header(self) -> Dict[str, Any]:
        """Get the full header, including signature
        If there is not signature already, will generate it, which requires
        to the private key of signed_by

        :return: The full drop metadata header in dict form
        """
        h = await self.unsigned_header
        if self.sig is None:
            self.log.debug("signing header")
            key = await node_init.load_private_key_from_disk()
            self.sig = await crypto_util.sign_dictionary(key, h)
        h["header_signature"] = self.sig
        return h

    async def verify_header(self) -> None:
        """Verify the signature in the header

        If the signature is OK, returns none, if the signature is None or is
        invalid throws a VerificationException
        """
        if self.sig is None:
            self.log.error("header signature not found when verifying")
            raise VerificationException()
        key = await get_pub_key(self.signed_by)
        await crypto_util.verify_signed_dictionary(
            key, self.sig, (await self.unsigned_header),
        )

    def get_file_name_from_id(self, file_hash: bytes) -> str:
        """Get the file name of a file id

        :param file_hash: the file id
        :return: the file name string
        """
        for (fname, fhash) in self.files.items():
            if fhash == file_hash:
                return fname

        self.log.error("tried to lookup a file that doesn't exist")
        raise FileNotFoundError

    async def unsubscribe(self) -> None:
        """Removes the refrence in the .5yncr folder therefore preventing
        future updates

        :return: None
        """
        save_path = _get_save_path()
        encoded_drop_id = crypto_util.b64encode(self.id).decode('utf-8')
        drop_loc_file = os.path.join(save_path, encoded_drop_id)
        os.remove(drop_loc_file)

    async def delete(self) -> None:
        """Deletes the drop from the local system and unsubscribes

        :return: None
        """
        self.unsubscribe()
        drop_loc = await get_drop_location(self.id)
        self.log.debug("deleteing drop folder: %s", self.id)
        shutil.rmtree(drop_loc)

    @staticmethod
    def make_filename(
        id: bytes, version: Union[str, DropVersion],
    ) -> str:
        """Make the filename for a drop metadata"""
        return "%s_%s" % (
            crypto_util.b64encode(id).decode("utf-8"), str(version),
        )

    async def write_file(
        self, metadata_location: str, is_latest: bool=True,
    ) -> None:
        """Write the representation of this objec to disk

        :param metadata_location: where to write to disk
        :param is_latest: whether to also write the LATEST file
        :return: None
        """
        self.log.debug("writing file")
        file_name = DropMetadata.make_filename(self.id, self.version)
        if not os.path.exists(metadata_location):
            os.makedirs(metadata_location)
        async with aiofiles.open(
            os.path.join(metadata_location, file_name), 'wb',
        ) as f:
            await f.write(await self.encode())
        if is_latest:
            await DropMetadata.write_latest(
                self.id, self.version, metadata_location,
            )

    @staticmethod
    async def write_latest(
        id: bytes, version: DropVersion,
        metadata_location: str,
    ) -> None:
        """Write the latest version to disk

        :param id: the drop id
        :param version: the latest version
        :para metadata_location: where to write it
        """
        file_name = DropMetadata.make_filename(id, LATEST)
        async with aiofiles.open(
            os.path.join(metadata_location, file_name), 'w',
        ) as f:
            to_write = DropMetadata.make_filename(id, version)
            await f.write(to_write)

    @staticmethod
    async def read_latest(
        id: bytes, metadata_location: str,
    ) -> Optional[str]:
        """Read the latest drop version

        :param id: the drop id
        :param metadata_location: where to find it
        """
        file_name = DropMetadata.make_filename(id, LATEST)
        logger.debug(
            "trying to read file %s from %s", file_name, metadata_location,
        )
        if not os.path.isfile(os.path.join(metadata_location, file_name)):
            logger.debug("File not found")
            return None
        async with aiofiles.open(
            os.path.join(metadata_location, file_name), 'r',
        ) as f:
            logger.debug("Reading file")
            return await f.readline()

    @staticmethod
    @async_cache()
    async def read_file(
        id: bytes, metadata_location: str, version: Optional[DropVersion]=None,
    ) -> Optional['DropMetadata']:
        """Read a drop metadata file from disk

        :param id: the drop id
        :param metadata_location: where to look for the file
        :param version: the drop version
        :return: A DropMetadata object, or maybe None
        """
        logger.debug("reading from file")
        if version is None:
            logger.debug(
                "Version is None, looking it up in %s", metadata_location,
            )
            file_name = await DropMetadata.read_latest(
                id, metadata_location,
            )
        else:
            logger.debug("Getting version %s", version)
            file_name = DropMetadata.make_filename(id, version)
        if file_name is None:
            logger.warning(
                "latest drop metadata not found for %s",
                crypto_util.b64encode(id),
            )
            return None

        if not os.path.isfile(os.path.join(metadata_location, file_name)):
            logger.warning(
                "drop metadata not found for %s",
                crypto_util.b64encode(id),
            )
            return None

        async with aiofiles.open(
            os.path.join(metadata_location, file_name), 'rb',
        ) as f:
            b = b''
            while True:
                data = await f.read()
                if not data:
                    break
                b += data
            return await DropMetadata.decode(b)

    async def encode(self) -> bytes:
        """Encode the full drop metadata file, including files, to bytes

        :return: The bencoded full metadata file
        """
        h = await self.header
        h["files"] = self.files
        return bencode.encode(h)

    @staticmethod
    async def decode(b: bytes) -> 'DropMetadata':
        """Decodes a bencoded drop metadata file to a DropMetadata object
        Also verifies the files hash and header signature, and throws an
        exception if they're not OK

        :param b: The bencoded file
        :return: A DropMetadata object from b
        """
        # Note: assumes signed header
        decoded = bencode.decode(b)
        dm = DropMetadata(
            drop_id=decoded["drop_id"],
            name=decoded["name"],
            version=DropVersion(decoded["version"], decoded["version_nonce"]),
            previous_versions=[
                DropVersion(
                    v["version"],
                    v["nonce"],
                ) for v in decoded["previous_versions"]
            ],
            primary_owner=decoded["primary_owner"],
            other_owners=decoded["other_owners"],
            signed_by=decoded["signed_by"],
            files_hash=decoded["files_hash"],
            files=decoded["files"],
            sig=decoded["header_signature"],
        )
        await dm.verify_files_hash()
        await dm.verify_header()
        return dm


async def save_drop_location(drop_id: bytes, location: str) -> None:
    """Save a drop's location in the central data dir

    :param drop_id: The unencoded drop id
    :param location: Where the drop is located on disk
    """
    save_path = _get_save_path()

    encoded_drop_id = crypto_util.b64encode(drop_id).decode('utf-8')

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    async with aiofiles.open(
        os.path.join(save_path, encoded_drop_id), 'w',
    ) as f:
        await f.write(location)


async def get_drop_location(drop_id: bytes) -> str:
    """Get a drop's location from the central data dir

    :param drop_id: The drop id to look up
    :return: The drops save dir
    """
    save_path = _get_save_path()

    encoded_drop_id = crypto_util.b64encode(drop_id).decode('utf-8')

    async with aiofiles.open(
        os.path.join(save_path, encoded_drop_id), 'r',
    ) as f:
        return await f.read()


def list_drops() -> List[bytes]:
    """
    List the drops on this node

    :return: List of drop IDs
    """
    save_path = _get_save_path()
    names = os.listdir(save_path)

    return [crypto_util.b64decode(os.fsencode(e)) for e in names]


def _get_save_path() -> str:
    node_info_path = node_init.get_full_init_directory()
    save_path = os.path.join(node_info_path, DEFAULT_METADATA_LOOKUP_LOCATION)
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    return save_path


async def get_pub_key(node_id: bytes) -> crypto_util.rsa.RSAPublicKey:
    """
    Gets the public key from disk if possible otherwise request it from
    PublicKeyStore

    :param node_id: bytes for the node you want public key of
    :return: PublicKey
    """
    init_directory = get_full_init_directory(None)
    pub_key_directory = os.path.join(
        init_directory,
        DEFAULT_PUB_KEY_LOOKUP_LOCATION,
    )

    if not os.path.isdir(pub_key_directory):
        os.makedirs(pub_key_directory)

    key_file_name = "{}.pub".format(crypto_util.b64encode(node_id))
    key_path = os.path.join(pub_key_directory, key_file_name)

    if os.path.isfile(key_path):
        async with aiofiles.open(key_path, 'rb') as pub_file:
            pub_key = await pub_file.read()
            return load_public_key(pub_key)
    else:
        key_bytes = await load_private_key_from_disk()
        this_node_id = await node_id_from_private_key(key_bytes)
        public_key_store = await get_public_key_store(this_node_id)
        key_request = await public_key_store.request_key(node_id)
        if key_request[0] and key_request[1] is not None:
            pub_key = key_request[1].encode('utf-8')
            await _save_key_to_disk(key_path, pub_key)
            return load_public_key(pub_key)
        else:
            raise VerificationException()


async def send_my_pub_key() -> None:
    """Send the pub key for this node the the Key Store"""
    this_node_id = await node_id_from_private_key(
        await load_private_key_from_disk(),
    )
    logger.info(
        "Sending pub key for %s to tracker",
        crypto_util.b64encode(this_node_id),
    )
    public_key_store = await get_public_key_store(this_node_id)
    pub_key = (await load_private_key_from_disk()).public_key()
    pub_key_bytes = crypto_util.dump_public_key(pub_key)
    await public_key_store.set_key(pub_key_bytes)


async def _save_key_to_disk(key_path: str, pub_key: bytes) -> None:
    """
    Saves the public key to the specified location
    :param key_path: absolute path to location of public key
    :param pub_key: bytes to be saved
    """
    async with aiofiles.open(key_path, 'wb') as pub_file:
        await pub_file.write(pub_key)


def gen_drop_id(first_owner: bytes) -> bytes:
    """Geterate a drop id"""
    return first_owner + crypto_util.random_bytes()
