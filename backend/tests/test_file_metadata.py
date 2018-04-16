from syncr_backend.metadata.file_metadata import DEFAULT_CHUNK_SIZE
from syncr_backend.metadata.file_metadata import FileMetadata


def test_file_metadata_decode() -> None:
    i = b'd10:chunk_sizei8388608e6:chunksl4:01234:1234e7:drop_id3:foo7:'\
        b'file_id4:000011:file_lengthi100e16:protocol_versioni1ee'

    f = FileMetadata.decode(i)

    assert len(f.hashes) == 2
    assert f.file_length == 100
    assert f.chunk_size == DEFAULT_CHUNK_SIZE


def test_file_metadata_encode() -> None:
    i = b'd10:chunk_sizei8388608e6:chunksl4:01234:1234e7:drop_id3:foo7:'\
        b'file_id4:000011:file_lengthi100e16:protocol_versioni1ee'

    f = FileMetadata([b'0123', b'1234'], b'0000', 100, b'foo')

    assert f.encode() == i
