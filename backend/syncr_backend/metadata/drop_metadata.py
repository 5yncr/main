"The dorp metadata object and related functions"""
import logging
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_METADATA_LOOKUP_LOCATION
from syncr_backend.constants import DEFAULT_PUB_KEY_LOOKUP_LOCATION
from syncr_backend.external_interface.public_key_store import \
    get_public_key_store
from syncr_backend.init import node_init
from syncr_backend.init.node_init import get_full_init_directory
from syncr_backend.init.node_init import load_private_key_from_disk
from syncr_backend.util import crypto_util
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

    def __iter__(self):
        """Used for calling dict() on this object, so it becomes
        {'version': version, 'nonce': nonce}
        """
        yield 'version', self.version
        yield 'nonce', self.nonce

    def __str__(self):
        return "%s_%s" % (self.version, self.nonce)


class DropMetadata(object):

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

    @property
    def log(self) -> logging.Logger:
        return get_logger(
            '.'.join([
                __name__, self.__class__.__name__,
                crypto_util.b64encode(self.id).decode('utf-8'),
            ]),
        )

    @property
    def files_hash(self) -> bytes:
        """Generate the hash of the files dictionary

        :return: The hash of the bencoded files dict
        """
        if self._files_hash is not None:
            return self._files_hash
        else:
            h = self._gen_files_hash()
            self._files_hash = h
            return h

    def _gen_files_hash(self) -> bytes:
        return crypto_util.hash_dict(self.files)

    def verify_files_hash(self) -> None:
        """Verify the file hash in this object

        Returns None if the hash is OK, throwns an exception if the hash is not
        good or has not been set
        """
        if self._files_hash is None:
            self.log.error("no files hash found when verifying")
            raise VerificationException()
        given = self._files_hash
        expected = self._gen_files_hash()
        if given != expected:
            self.log.error("files verification failed!")
            raise VerificationException()

    @property
    def unsigned_header(self) -> Dict[str, Any]:  # TODO: type this better?
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
            "files_hash": self.files_hash,
            "files": {},
        }
        return h

    @property
    def header(self) -> Dict[str, Any]:
        """Get the full header, including signature
        If there is not signature already, will generate it, which requires
        to the private key of signed_by

        :return: The full drop metadata header in dict form
        """
        h = self.unsigned_header
        if self.sig is None:
            self.log.debug("signing header")
            key = node_init.load_private_key_from_disk()
            self.sig = crypto_util.sign_dictionary(key, h)
        h["header_signature"] = self.sig
        return h

    def verify_header(self) -> None:
        """Verify the signature in the header

        If the signature is OK, returns none, if the signature is None or is
        invalid throws an exception
        """
        if self.sig is None:
            self.log.error("header signature not found when verifying")
            raise VerificationException()
        key = get_pub_key(self.signed_by)
        crypto_util.verify_signed_dictionary(
            key, self.sig, self.unsigned_header,
        )

    def get_file_name_from_id(self, file_hash) -> str:
        """Get the file name of a file id

        :param file_hash: the file id
        :return: the file name string
        """
        for (fname, fhash) in self.files.items():
            if fhash == file_hash:
                return fname

        self.log.error("tried to lookup a file that doesn't exist")
        raise FileNotFoundError

    @staticmethod
    def make_filename(
        id: bytes, version: Union[str, DropVersion],
    ) -> str:
        return "%s_%s" % (
            crypto_util.b64encode(id).decode("utf-8"), str(version),
        )

    def write_file(
        self, metadata_location: str, is_latest: bool=True,
    ) -> None:
        """Write the representation of this objec to disk

        :param metadata_location: where to write to disk
        :return: None
        """
        self.log.debug("writing file")
        file_name = DropMetadata.make_filename(self.id, self.version)
        if not os.path.exists(metadata_location):
            os.makedirs(metadata_location)
        with open(os.path.join(metadata_location, file_name), 'wb') as f:
            f.write(self.encode())
        if is_latest:
            DropMetadata.write_latest(self.id, self.version, metadata_location)

    @staticmethod
    def write_latest(
        id: bytes, version: DropVersion,
        metadata_location: str,
    ) -> None:
        """Write the latest version to disk

        :param id: the drop id
        :param version: the latest version
        :para metadata_location: where to write it
        """
        file_name = DropMetadata.make_filename(id, LATEST)
        with open(os.path.join(metadata_location, file_name), 'w') as f:
            to_write = DropMetadata.make_filename(id, version)
            f.write(to_write)

    @staticmethod
    def read_latest(
        id: bytes, metadata_location: str,
    ) -> Optional[str]:
        """Read the latest drop version

        :param id: the drop id
        :param metadata_location: where to find it
        """
        file_name = DropMetadata.make_filename(id, LATEST)
        if not os.path.isfile(os.path.join(metadata_location, file_name)):
            return None
        with open(os.path.join(metadata_location, file_name), 'r') as f:
            return f.readline()

    @staticmethod
    def read_file(
        id: bytes, metadata_location: str, version: Optional[DropVersion]=None,
    ) -> Optional['DropMetadata']:
        """Read a drop metadata file from disk

        :param id: the drop id
        :param version: the drop version
        :param metadata_location: where to look for the file
        :return: A DropMetadata object, or maybe None
        """
        logger.debug("reading from file")
        if version is None:
            file_name = DropMetadata.read_latest(id, metadata_location)
        else:
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

        with open(os.path.join(metadata_location, file_name), 'rb') as f:
            b = b''
            while True:
                data = f.read(65536)
                if not data:
                    break
                b += data
            return DropMetadata.decode(b)

    def encode(self) -> bytes:
        """Encode the full drop metadata file, including files, to bytes

        :return: The bencoded full metadata file
        """
        h = self.header
        h["files"] = self.files
        return bencode.encode(h)

    @staticmethod
    def decode(b: bytes) -> 'DropMetadata':
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
                    v["version_nonce"],
                ) for v in decoded["previous_versions"]
            ],
            primary_owner=decoded["primary_owner"],
            other_owners=decoded["other_owners"],
            signed_by=decoded["signed_by"],
            files_hash=decoded["files_hash"],
            files=decoded["files"],
            sig=decoded["header_signature"],
        )
        dm.verify_files_hash()
        dm.verify_header()
        return dm


def save_drop_location(drop_id: bytes, location: str) -> None:
    """Save a drops location in the central data dir

    :param drop_id: The unencoded drop id
    :param location: Where the drop is located on disk
    """
    save_path = _get_save_path()

    encoded_drop_id = crypto_util.b64encode(drop_id).decode('utf-8')

    if not os.path.exists(save_path):
        os.makedirs(save_path)

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


def get_pub_key(node_id: bytes) -> crypto_util.rsa.RSAPublicKey:
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

    key_file_name = "{}.pub".format(node_id)
    key_path = os.path.join(pub_key_directory, key_file_name)

    if os.path.isfile(key_path):
        with open(key_path, 'rb') as pub_file:
            pub_key = pub_file.read()
            return load_public_key(pub_key)
    else:
        node_id = node_id_from_private_key(load_private_key_from_disk())
        public_key_store = get_public_key_store(node_id)
        key_request = public_key_store.request_key(bytes)
        if key_request[0]:
            pub_key = key_request[1]
            _save_key_to_disk(key_path, pub_key)
            return load_public_key(pub_key)
        else:
            raise VerificationException()


def _save_key_to_disk(key_path: str, pub_key: bytes) -> None:
    """
    Saves the public key to the specified location
    :param key_path: absolute path to location of public key
    :param pub_key: bytes to be saved
    """
    with open(key_path, 'wb') as pub_file:
        pub_file.write(pub_key)


def gen_drop_id(first_owner: bytes) -> bytes:
    """Geterate a drop id"""
    return first_owner + crypto_util.random_bytes()
