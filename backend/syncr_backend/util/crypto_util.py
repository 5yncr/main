"""Functions for dealing with hashes/keys/ids in a consistant manner"""
import asyncio
import base64
import hashlib
import os
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import bencode  # type: ignore
from cryptography.exceptions import InvalidSignature  # type: ignore
from cryptography.hazmat.backends import default_backend  # type: ignore
from cryptography.hazmat.primitives import hashes  # type: ignore
from cryptography.hazmat.primitives import serialization  # type: ignore
from cryptography.hazmat.primitives.asymmetric import padding  # type: ignore
from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore

from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)

B64_ALT_CHARS = b'+-'


class VerificationException(Exception):
    """To be raised when a hash or signature verification fails"""
    pass


async def hash(b: bytes) -> bytes:
    """Default hash function

    >>> from syncr_backend.util.crypto_util import hash, b64encode
    >>> import asyncio
    >>> loop = asyncio.get_event_loop()
    >>> b64encode(loop.run_until_complete(hash(b"foo")))
    b'LCa0a2j-xo-5m0U8HTBBNBNCLXBkg7+g+YpeiGJm564='

    :param b: The bytes to hash
    :return: The hash of b
    """
    loop = asyncio.get_event_loop()
    logger.debug("hashing bytes of len %s", len(b))
    return await loop.run_in_executor(None, _hash, b)


def _hash(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


async def hash_dict(d: Dict[str, Any]) -> bytes:
    """Hash a dictionary, by first bencoding it

    >>> from syncr_backend.util.crypto_util import hash_dict, b64encode
    >>> import asyncio
    >>> loop = asyncio.get_event_loop()
    >>> b64encode(loop.run_until_complete(hash_dict({'key': b"foo"})))
    b'gqcj3O1NwwlHhSJFHUi3eiJ5++9Pom-aIqN1QRPdLRo='

    :param b: The dictionary to hash
    :return: The hash of bencode(b)
    """
    logger.debug("hashing dict of len %s", len(d))
    return await hash(bencode.encode(d))


def b64encode(b: bytes) -> bytes:
    """Encode a binary sequence for humans to read

    :param b: The sequence to encode
    :return: An encoded sequence
    """
    return base64.b64encode(b, altchars=B64_ALT_CHARS)


def b64decode(b: bytes) -> bytes:
    """Decode a b64 sequence back into binary

    >>> from syncr_backend.util.crypto_util import b64encode, b64decode
    >>> data = b'IamImportantData'
    >>> encoded_data = b64encode(data)
    >>> encoded_data
    b'SWFtSW1wb3J0YW50RGF0YQ=='
    >>> b64decode(encoded_data)
    b'IamImportantData'

    :param b: The encoded sequence
    :return: The decoded bytes
    """
    return base64.b64decode(b, altchars=B64_ALT_CHARS)


encode_peerlist_prefix = b'type:peerlist'


def encode_peerlist(
    peerlist: List[Tuple[Any, str, int]],
) -> bytes:
    """
    encodes peerlist into bytes to put in dht

    :param peerlist: list of dht peers
    :return: bytes of encoded peerlist
    """
    return encode_peerlist_prefix + bencode.encode(list(peerlist))


def decode_peerlist(rawpl: bytes) -> Optional[List[Any]]:
    """
    decodes peerlist from bytes representation to list

    >>> from syncr_backend.util.crypto_util import encode_peerlist
    >>> from syncr_backend.util.crypto_util import decode_peerlist
    >>> peers = [('foo', '1.2.3.4', 2), ('bar', '2.3.4.5', 3)]
    >>> encoded_peers = encode_peerlist(peers)
    >>> encoded_peers
    b'type:peerlistll3:foo7:1.2.3.4i2eel3:bar7:2.3.4.5i3eee'
    >>> decode_peerlist(encoded_peers)
    [('foo', '1.2.3.4', 2), ('bar', '2.3.4.5', 3)]

    :param rawpl: bytes form of peerlist
    :return: A list of peers, or None
    """
    if rawpl[:len(encode_peerlist_prefix)] == encode_peerlist_prefix:
        peerlist = rawpl[len(encode_peerlist_prefix):]
    else:
        return None
    try:
        declist = bencode.decode(peerlist)

        return list(map(lambda x: tuple(x), declist))
    except Exception:
        return None


def random_bytes() -> bytes:
    """Generate 32 random bytes

    :returns: 32 random bytes
    """
    return os.urandom(32)


def random_int() -> int:
    """Generate a random integer

    >>> from syncr_backend.util.crypto_util import random_int
    >>> random_int()  # doctest: +SKIP
    11520214175276372604

    :returns: a random 64 bit int
    """
    return int.from_bytes(os.urandom(8), 'big')


def load_public_key(key: bytes) -> rsa.RSAPublicKey:
    """Load a public key from bytes

    :param key: The serialized key
    :return: The RSAPublicKey object of the key
    """
    return serialization.load_pem_public_key(key, backend=default_backend())


def load_private_key(key: bytes) -> rsa.RSAPrivateKey:
    """Load a private key from bytes

    :param key: The serialized key
    :return: The RSAPrivateKey object of the key
    """
    return serialization.load_pem_private_key(
        key,
        None,
        backend=default_backend(),
    )


def dump_public_key(key: rsa.RSAPublicKey) -> bytes:
    """Dump a public key to PEM format (text)

    :param key: An RSAPrivateKey to dump the public key of
    :return: The dumped bytes of the public key, as PEM
    """
    return key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def dump_private_key(key: rsa.RSAPrivateKey) -> bytes:
    """Dump a private key to PEM format (text)

    :param key: The Private Key objec to dump
    :return: The bytes of the private key, as PEM
    """
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


async def node_id_from_public_key(key: rsa.RSAPublicKey) -> bytes:
    """Generate a node id from a public key
    It uses the default dump, and hashes that

    :param key: The Public key to generate the nodeid from
    :return: The nodeid, as bytes
    """
    key_serial = dump_public_key(key)
    return await hash(key_serial)


async def generate_private_key() -> rsa.RSAPrivateKey:
    """Generate a public and private key

    :return: A new RSAPrivateKey
    """
    loop = asyncio.get_event_loop()
    private_key = await loop.run_in_executor(None, _generate_private_key)

    return private_key


def _generate_private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=4048,
        backend=default_backend(),
    )


async def sign_dictionary(
    private_key: rsa.RSAPrivateKey,
    dictionary: Dict[str, Any],
) -> bytes:
    """
    Takes a dict and returns a rsa signature of the hash of the dict

    :param private_key: RSA private_key
    :param dictionary: the dictionary to sign
    :return: signature of the dictionary
    """
    signature_interface = private_key.signer(
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    signature_interface.update(await hash(bencode.encode(dictionary)))
    return signature_interface.finalize()


async def verify_signed_dictionary(
    public_key: rsa.RSAPublicKey,
    signature: bytes,
    dictionary: Dict[str, Any],
) -> None:
    """
    Returns None if success,
    else throws cryptography.exceptions.InvalidSignature

    :param public_key: RSA public_key
    :param signature: the signature of the dictionary
    :param dictionary: the actual dictionary
    :raises VerificationException: If the verification fails
    :return: None
    """
    verifier = public_key.verifier(
        signature,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    verifier.update(await hash(bencode.encode(dictionary)))
    try:
        verifier.verify()
    except InvalidSignature:
        raise VerificationException()


async def node_id_from_private_key(key: rsa.RSAPrivateKey) -> bytes:
    """Wrapper to get the node id from the private key"""
    return await node_id_from_public_key(key.public_key())


async def verify_node_id(key: rsa.RSAPublicKey, node_id: bytes) -> bool:
    """Verify a node id from a public key"""
    # TODO: BUG: use something better than == here (something constant time
    #  and secure)
    return await node_id_from_public_key(key) == node_id
