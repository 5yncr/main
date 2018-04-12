#!/usr/bin/env python
import argparse
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

    id = drop_init.initialize_drop(args.directory)
    sys.stdout.write("%s" % id.decode('utf-8'))
    sys.stdout.flush()


if __name__ == '__main__':
    main()
