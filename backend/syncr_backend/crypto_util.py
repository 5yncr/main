# Functions for dealing with hashes/keys/ids in a consistant manner
import base64
import hashlib

from cryptography.hazmat.backends import default_backend  # type: ignore
from cryptography.hazmat.primitives import serialization  # type: ignore
from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore

B64_ALT_CHARS = b'+-'


def hash(b: bytes) -> bytes:
    """Default hash function"""
    return hashlib.sha256(b).digest()


def b64encode(b: bytes) -> bytes:
    """Encode a binary sequence for humans to read"""
    return base64.b64encode(b, altchars=B64_ALT_CHARS)


def b64decode(b: bytes) -> bytes:
    """Decode a b64 sequence back into binary"""
    return base64.b64decode(b, altchars=B64_ALT_CHARS)


def load_public_key(key: bytes) -> rsa.RSAPublicKey:
    """Load a public key from bytes"""
    return serialization.load_pem_public_key(key, backend=default_backend())


def load_private_key(key: bytes) -> rsa.RSAPrivateKey:
    """Load a private key from bytes"""
    return serialization.load_pem_private_key(
        key,
        None,
        backend=default_backend(),
    )


def dump_public_key(key: rsa.RSAPrivateKey) -> bytes:
    """Dump a public key to PEM format (text)"""
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def dump_private_key(key: rsa.RSAPrivateKey) -> bytes:
    """Dump a private key to PEM format (text)"""
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def node_id_from_public_key(key: rsa.RSAPublicKey) -> bytes:
    """Generate a node id from a public key
    It uses the default dump, and hashes that
    """
    key_serial = dump_public_key(key)
    return hash(key_serial)


def generate_private_key() -> rsa.RSAPrivateKey:
    """Generate a public and private key """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4048,
        backend=default_backend(),
    )

    return private_key


def node_id_from_private_key(key: rsa.RSAPrivateKey) -> bytes:
    """Wrapper to get the node id from the private key"""
    return node_id_from_public_key(key.public_key())


def verify_node_id(key: rsa.RSAPublicKey, node_id: bytes) -> bool:
    """Verify a node id from a public key"""
    # TODO: BUG: use something better than == here (something constant time
    #  and secure)
    return node_id_from_public_key(key) == node_id
