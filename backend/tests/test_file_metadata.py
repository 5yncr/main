import hashlib
import tempfile

from syncr_backend.file_metadata import DEFAULT_CHUNK_SIZE
from syncr_backend.file_metadata import FileMetadata
from syncr_backend.file_metadata import hash_file


def test_hash_file():
    with tempfile.TemporaryFile() as f:
        f.write(b'x\11' * 1001)
        f.seek(0)

        h_out = hash_file(f)
        expected_data = b'x\11' * 1001
        h_expected = hashlib.sha256(expected_data).digest()

        assert len(h_out) == 1
        assert h_out[0] == h_expected


def test_file_metadata_decode():
    i = b"d10:chunk_sizei8388608e6:chunksl4:01234:1234e11:"\
        b"file_lengthi100e16:protocol_versioni1ee"

    f = FileMetadata.decode(i)

    assert len(f.hashes) == 2
    assert f.file_length == 100
    assert f.chunk_size == DEFAULT_CHUNK_SIZE


def test_file_metadata_encode():
    i = b"d10:chunk_sizei8388608e6:chunksl4:01234:1234e11:"\
        b"file_lengthi100e16:protocol_versioni1ee"

    f = FileMetadata([b'0123', b'1234'], 100)

    assert f.encode() == i
