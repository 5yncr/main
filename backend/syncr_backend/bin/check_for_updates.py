#!/usr/bin/env python
import argparse
import asyncio

from syncr_backend.util import crypto_util
from syncr_backend.util import drop_util


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check for updates for a drop",
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

    # TODO: print a list of what's changed
    md, update_avail = loop.run_until_complete(
        drop_util.check_for_update(drop_id),
    )
    if update_avail:
        print("Update available: %s. Run update_drop" % md.version.version)
    else:
        print("No update available")


if __name__ == '__main__':
    main()
