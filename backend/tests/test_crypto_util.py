from syncr_backend import crypto_util


def test_signature():
    rsa_private_key = crypto_util.generate_private_key()
    d = {
        'a': 1,
        'b': 2,
        'c': 3,
    }
    signature = crypto_util.sign_dictionary(rsa_private_key, d)
    crypto_util.verify_signed_dictionary(
        rsa_private_key.public_key(),
        signature,
        d,
    )
