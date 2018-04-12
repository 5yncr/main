#!/usr/env/bin/python
import argparse
import os

from syncr_backend.constants import DEFAULT_DROP_METADATA_LOCATION
from syncr_backend.constants import DEFAULT_FILE_METADATA_LOCATION
from syncr_backend.metadata.drop_metadata import DropMetadata
from syncr_backend.metadata.drop_metadata import get_drop_location
from syncr_backend.metadata.file_metadata import FileMetadata
from syncr_backend.util import crypto_util
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "drop_id",
        type=str,
        help="b64 encoded Drop ID",
    )
    args = parser.parse_args()

    drop_id = crypto_util.b64decode(args.drop_id.encode('utf-8'))
    drop_location = get_drop_location(drop_id)
    metadata_dir = os.path.join(drop_location, DEFAULT_DROP_METADATA_LOCATION)
    file_metadata_dir = os.path.join(
        drop_location, DEFAULT_FILE_METADATA_LOCATION,
    )
    metadata = DropMetadata.read_file(drop_id, metadata_dir)

    if metadata is None:
        logger.error("Drop metadata not found, failing")
        exit(1)

    for file_name, file_id in metadata.files.items():
        file_metadata = FileMetadata.read_file(file_id, file_metadata_dir)

        if file_metadata is None:
            logger.error("File metadata for %s not found, exiting", file_name)
            exit(1)

        file_metadata.file_name = file_name

        needed_chunks = file_metadata.needed_chunks
        if needed_chunks:
            logger.error(
                "File %s has needed chunks %s, exiting", file_name,
                needed_chunks,
            )
            exit(1)

    logger.info("All good, exiting with success")
    exit(0)


if __name__ == '__main__':
    main()
