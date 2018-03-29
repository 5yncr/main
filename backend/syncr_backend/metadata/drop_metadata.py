"The dorp metadata object and related functions"""
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

import bencode  # type: ignore

from syncr_backend.constants import DEFAULT_METADATA_LOOKUP_LOCATION
from syncr_backend.init import node_init
from syncr_backend.util import crypto_util
from syncr_backend.util.crypto_util import VerificationException


LATEST = "LATEST"


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
            raise VerificationException()
        given = self._files_hash
        expected = self._gen_files_hash()
        if given != expected:
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
    ) -> str:
        """Read the latest drop version

        :param id: the drop id
        :param metadata_location: where to find it
        """
        file_name = DropMetadata.make_filename(id, LATEST)
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
        if version is None:
            file_name = DropMetadata.read_latest(id, metadata_location)
        else:
            file_name = DropMetadata.make_filename(id, version)

        if not os.path.exists(os.path.join(metadata_location, file_name)):
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
        os.mkdir(save_path)

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


def get_pub_key(nodeid: bytes) -> crypto_util.rsa.RSAPublicKey:
    raise NotImplementedError()


def gen_drop_id(first_owner: bytes) -> bytes:
    """Geterate a drop id"""
    return first_owner + crypto_util.random_bytes()
