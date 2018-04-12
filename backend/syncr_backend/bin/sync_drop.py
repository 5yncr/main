#!/usr/bin/env python
import argparse

from syncr_backend.util import crypto_util
from syncr_backend.util import drop_util


def main() -> None:
    parser = argparse.ArgumentParser()
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
    args = parser.parse_args()

    id = crypto_util.b64decode(args.drop_id.encode('utf-8'))
    done = drop_util.sync_drop(id, args.directory)

    if done:
        print("Drop successfully synced")
    else:
        print("Drop not completed, re-run command")


if __name__ == '__main__':
    main()
