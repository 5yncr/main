import os
import tempfile

from syncr_backend import crypto_util
from syncr_backend import node_init


def test_node_init():

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        node_init.initialize_node()


def test_rsa_loading_and_saving():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        os.mkdir(".node")
        private_key = crypto_util.generate_private_key()
        node_init.write_private_key_to_disk(private_key, ".node/")
        assert crypto_util.dump_private_key(
            private_key,
        ) == crypto_util.dump_private_key(
            node_init.load_private_key_from_disk(".node/"),
        )
