import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import bencode  # type: ignore

from syncr_backend import crypto_util
from syncr_backend import node_init
from syncr_backend import util
from syncr_backend.crypto_util import VerificationException
from syncr_backend.file_metadata import FileMetadata
from syncr_backend.file_metadata import make_file_metadata


class DropVersion(object):

    def __init__(self, version: int, nonce: int) -> None:
        self.version = version
        self.nonce = nonce

    def __iter__(self):
        yield 'version', self.version
        yield 'nonce', self.nonce


class DropMetadata(object):

    def __init__(
        self, drop_id: bytes, name: str, version: DropVersion,
        previous_versions: List[DropVersion], primary_owner: bytes,
        other_owners: Dict[bytes, int], signed_by: bytes,
        files: Dict[str, bytes], files_hash: Optional[bytes]=None,
        sig: Optional[bytes]=None, protocol_version: int=1,
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

    def write_file(self, metadata_location: bytes):
        file_name = crypto_util.b64encode(self.id)
        if not os.path.exists(metadata_location):
            os.makedirs(metadata_location)
        with open(os.path.join(metadata_location, file_name), 'wb') as f:
            f.write(self.encode())


def get_pub_key(nodeid: bytes) -> crypto_util.rsa.RSAPublicKey:
    raise NotImplementedError()


def gen_drop_id(first_owner: bytes) -> bytes:
    return first_owner + crypto_util.random_bytes()


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
    files = {}
    for (dirpath, filename) in util.walk_with_ignore(path, ignore):
        full_name = os.path.join(dirpath, filename)
        files[full_name] = make_file_metadata(full_name)

    file_hashes = {name: m.file_hash for (name, m) in files.items()}
    drop_id = gen_drop_id(owner)
    dm = DropMetadata(
        drop_id=drop_id,
        name=drop_name,
        version=DropVersion(1, crypto_util.random_int()),
        previous_versions=[],
        primary_owner=owner,
        other_owners=other_owners,
        signed_by=owner,
        files=file_hashes,
    )

    return (dm, files)
