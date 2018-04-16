#!/usr/bin/env python
import argparse
import asyncio
import sys

from syncr_backend.init import drop_init


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to create a drop from",
    )
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    id = loop.run_until_complete(drop_init.initialize_drop(args.directory))
    sys.stdout.write("%s" % id.decode('utf-8'))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
