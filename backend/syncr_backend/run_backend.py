#!/usr/bin/env python
import argparse
from typing import List

from syncr_backend import node_init


def execute_node_function(function_name: str, args: List[str]):
    """
    Runs a function with the given args

    :param function_name: string name of the function to run
    :param args: arguments for the function to run
    """

    # for functions that create or destroy the init directory
    init_function_map = {
        "node_init": node_init.initialize_node,
        "node_force_init": node_init.force_initialize_node,
        "delete_node": node_init.delete_node_directory,
    }
    if function_name in init_function_map:
        # handles up to one argument
        init_function_map[function_name](*args[:1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "function",
        type=str,
        nargs=1,
        help="string name of the function to be ran",
    )

    parser.add_argument(
        "--args",
        type=str,
        nargs='*',
        help='arguments for the function to be ran',
    )
    args = parser.parse_args()
    if args.args is not None:
        execute_node_function(args.function[0], args.args)
    else:
        execute_node_function(args.function[0], [])


if __name__ == '__main__':
    main()
