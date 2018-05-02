#!/usr/bin/env python
import argparse
import asyncio

from syncr_backend.util import crypto_util
from syncr_backend.util import drop_util


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a drop.  Does not run the backend to listen for "
        "incomming requests, only sends outgoing requests",
    )
    parser.add_argument(
        "drop_id",
        type=str,
        help="b64 encoded drop ID",
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Directory to save the drop to",
    )
    return parser


def main() -> None:
    args = parser().parse_args()

    loop = asyncio.get_event_loop()

    id = crypto_util.b64decode(args.drop_id.encode('utf-8'))

    done = loop.run_until_complete(drop_util.sync_drop(id, args.directory))

    if done:
        print("Drop successfully synced")
    else:
        print("Drop not completed, re-run command")


if __name__ == '__main__':
    main()
