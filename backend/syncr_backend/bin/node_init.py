#!/usr/bin/env python
import argparse

from syncr_backend.init import node_init


def main() -> None:
    parser = argparse.ArgumentParser()
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
    args = parser.parse_args()

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
