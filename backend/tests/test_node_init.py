import os
import tempfile

from syncr_backend.util import crypto_util
from syncr_backend.init import node_init


def test_node_init():

    with tempfile.TemporaryDirectory() as tmpdir:
        node_init.initialize_node(os.path.join(tmpdir, "test/",))


def test_rsa_loading_and_saving():
    with tempfile.TemporaryDirectory() as tmpdir:
        private_key = crypto_util.generate_private_key()
        node_init.write_private_key_to_disk(private_key, tmpdir)
        assert crypto_util.dump_private_key(
            private_key,
        ) == crypto_util.dump_private_key(
            node_init.load_private_key_from_disk(tmpdir),
        )
