#!/usr/bin/env python
import argparse
import asyncio
import os
import sys

from syncr_backend.init import drop_init


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize a drop by creating the necessary metadata "
        "files and storing metadata in the central config dir.",
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to create a drop from",
    )
    return parser


def main() -> None:
    args = parser().parse_args()

    loop = asyncio.get_event_loop()
    path = os.path.abspath(args.directory)
    id = loop.run_until_complete(drop_init.initialize_drop(path))
    sys.stdout.write("%s" % id.decode('utf-8'))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
