#!/usr/env/bin/python
import argparse
import asyncio
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
    loop = asyncio.get_event_loop()
    loop.run_until_complete(a_main())


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check the contents of a drop, returning status 0 if all "
        "the files are downloaded and correct, 1 otherwise (with a message).",
    )
    parser.add_argument(
        "drop_id",
        type=str,
        help="b64 encoded Drop ID",
    )
    return parser


async def a_main() -> None:
    """Lots to await on, so call this whole function in a run_until_complete"""
    args = parser().parse_args()

    id_prefix = b'dropid:'

    drop_id = args.drop_id.encode('utf-8')
    if drop_id.startswith(id_prefix):
        drop_id = crypto_util.b64decode(drop_id[len(id_prefix):])
    else:
        raise ValueError("drop Id must start with prefix 'dropid:'")

    drop_location = await get_drop_location(drop_id)
    metadata_dir = os.path.join(drop_location, DEFAULT_DROP_METADATA_LOCATION)
    file_metadata_dir = os.path.join(
        drop_location, DEFAULT_FILE_METADATA_LOCATION,
    )
    metadata = await DropMetadata.read_file(
        id=drop_id, metadata_location=metadata_dir,
    )

    if metadata is None:
        logger.error("Drop metadata not found, failing")
        exit(1)

    for file_name, file_id in metadata.files.items():
        file_metadata = await FileMetadata.read_file(
            file_id=file_id, metadata_location=file_metadata_dir,
            file_name=file_name,
        )

        if file_metadata is None:
            logger.error("File metadata for %s not found, exiting", file_name)
            exit(1)

        file_metadata.file_name = file_name

        needed_chunks = await file_metadata.needed_chunks
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
