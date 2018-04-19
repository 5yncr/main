import asyncio
import os

from syncr_backend.util import crypto_util


def test_encode_bad_input() -> None:
    f = os.urandom(12)
    fs = crypto_util.encode_peerlist_prefix + f
    dpl = crypto_util.decode_peerlist(f)
    dpl2 = crypto_util.decode_peerlist(fs)
    assert dpl is None and dpl2 is None


def test_encode_frozenset() -> None:

    f = [('12', '1234', 123), ('asdf', 'asdf', 123), ]
    epl = crypto_util.encode_peerlist(f)
    dpl = crypto_util.decode_peerlist(epl)
    assert f == dpl


def test_signature() -> None:
    loop = asyncio.get_event_loop()
    rsa_private_key = loop.run_until_complete(
        crypto_util.generate_private_key(),
    )
    d = {
        'a': 1,
        'b': 2,
        'c': 3,
    }
    signature = loop.run_until_complete(
        crypto_util.sign_dictionary(rsa_private_key, d),
    )
    loop.run_until_complete(crypto_util.verify_signed_dictionary(
        rsa_private_key.public_key(),
        signature,
        d,
    ))
