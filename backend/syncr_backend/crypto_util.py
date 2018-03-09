# Functions for dealing with hashes/keys/ids in a consistant manner
import base64
import hashlib
import os
from typing import Any
from typing import Dict

import bencode  # type: ignore
from cryptography.exceptions import InvalidSignature  # type: ignore
from cryptography.hazmat.backends import default_backend  # type: ignore
from cryptography.hazmat.primitives import hashes  # type: ignore
from cryptography.hazmat.primitives import serialization  # type: ignore
from cryptography.hazmat.primitives.asymmetric import padding  # type: ignore
from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore

B64_ALT_CHARS = b'+-'


class VerificationException(Exception):
    pass


def hash(b: bytes) -> bytes:
    """Default hash function

    :param b: The bytes to hash
    :return: The hash of b
    """
    return hashlib.sha256(b).digest()


def hash_dict(b: Dict[str, Any]) -> bytes:
    """Hash a dictionary, by first bencoding it

    :param b: The dictionary to hash
    :return: The hash of bencode(b)
    """
    return hash(bencode.encode(b))


def b64encode(b: bytes) -> bytes:
    """Encode a binary sequence for humans to read

    :param b: The sequence to encode
    :return: An encoded sequence
    """
    return base64.b64encode(b, altchars=B64_ALT_CHARS)


def b64decode(b: bytes) -> bytes:
    """Decode a b64 sequence back into binary

    :param b: The encoded sequence
    :return: The decoded bytes
    """
    return base64.b64decode(b, altchars=B64_ALT_CHARS)


def random_bytes() -> bytes:
    """Generate 32 random bytes

    :returns: 32 random bytes
    """
    return os.urandom(32)


def random_int() -> int:
    """Generate a random integer

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


def node_id_from_public_key(key: rsa.RSAPublicKey) -> bytes:
    """Generate a node id from a public key
    It uses the default dump, and hashes that

    :param key: The Public key to generate the nodeid from
    :return: The nodeid, as bytes
    """
    key_serial = dump_public_key(key)
    return hash(key_serial)


def generate_private_key() -> rsa.RSAPrivateKey:
    """Generate a public and private key

    :return: A new RSAPrivateKey
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4048,
        backend=default_backend(),
    )

    return private_key


def sign_dictionary(
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

    signature_interface.update(hash(bencode.encode(dictionary)))
    return signature_interface.finalize()


def verify_signed_dictionary(
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
    verifier.update(hash(bencode.encode(dictionary)))
    try:
        verifier.verify()
    except InvalidSignature:
        raise VerificationException()


def node_id_from_private_key(key: rsa.RSAPrivateKey) -> bytes:
    """Wrapper to get the node id from the private key"""
    return node_id_from_public_key(key.public_key())


def verify_node_id(key: rsa.RSAPublicKey, node_id: bytes) -> bool:
    """Verify a node id from a public key"""
    # TODO: BUG: use something better than == here (something constant time
    #  and secure)
    return node_id_from_public_key(key) == node_id
