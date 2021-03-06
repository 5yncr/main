#!/usr/bin/env python
import argparse
import asyncio

from syncr_backend.util import crypto_util
from syncr_backend.util import drop_util


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Update a drop from changes on the filesystem. Must be "
        "the owner of the drop to run this. One of save dir and drop id "
        "should be provided.",
    )
    parser.add_argument(
        "--save_dir",
        type=str,
        required=False,
        help="Directory of drop to updated",
    )
    parser.add_argument(
        "--drop_id",
        type=str,
        required=False,
        help="Drop ID to update",
    )
    return parser


def main() -> None:
    args = parser().parse_args()
    loop = asyncio.get_event_loop()

    if not (args.drop_id or args.save_dir):
        print("Either drop id or save dir must be specified")
        exit(1)

    if args.drop_id:
        drop_id = args.drop_id.encode('utf-8')
        drop_id = crypto_util.b64decode(drop_id)
    if not args.drop_id:
        drop_id = drop_util.get_drop_id_from_directory(args.save_dir)

    if drop_id is None:
        print("Drop ID not found")
        exit(1)

    loop.run_until_complete(drop_util.make_new_version(drop_id))


if __name__ == '__main__':
    main()
