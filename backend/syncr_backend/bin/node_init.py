#!/usr/bin/env python
import argparse

from syncr_backend.init import node_init


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Initialize a node by creating necessary keys and config "
        "directories.  Only needs to be run once.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="force initialization, overwriting existing keys, etc",
    )
    parser.add_argument(
        "--directory",
        type=str,
        help="Directory to initialize in",
    )
    return parser


def main() -> None:
    args = parser().parse_args()

    if args.directory is not None:
        kwargs = {'init_directory': args.directory}
    else:
        kwargs = {}

    if args.force:
        node_init.force_initialize_node(**kwargs)
    else:
        try:
            node_init.initialize_node(**kwargs)
        except FileExistsError as e:
            print("This file seems to already exist: %s" % e)


if __name__ == '__main__':
    main()
