import asyncio

from syncr_backend.util import crypto_util


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
