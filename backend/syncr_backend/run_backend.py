#!/usr/bin/env python
import argparse
import threading
from typing import Any
from typing import List

from syncr_backend.init import drop_init
from syncr_backend.init import node_init
from syncr_backend.network.listen_requests import listen_requests
from syncr_backend.util import crypto_util
from syncr_backend.util import drop_util
# from syncr_backend.network import send_requests


def run_backend() -> None:
    """
    Runs the backend
    """
    input_args_parser = argparse.ArgumentParser()
    input_args_parser.add_argument(
        "ip",
        type=str,
        nargs=1,
        help='ip to bind listening server',
    )
    input_args_parser.add_argument(
        "port",
        type=str,
        nargs=1,
        help='port to bind listening server',
    )
    input_args_parser.add_argument(
        "--backendonly",
        action="store_true",
        help='runs only the backend if added as an option',
    )
    arguments = input_args_parser.parse_args()

    shutdown_flag = threading.Event()
    request_listen_thread = threading.Thread(
        target=listen_requests,
        args=[arguments.ip[0], arguments.port[0], shutdown_flag],
    )
    request_listen_thread.start()

    if not arguments.backendonly:
        read_cmds_from_cmdline()
        shutdown_flag.set()
        request_listen_thread.join()


def read_cmds_from_cmdline() -> None:
    """
    Read and execute commands given as cmdline input
    """
    exit_flag = False
    while not exit_flag:
        command = input("5yncr >>> ").split(' ')
        return_list = ["", []]
        parse_cmd_thread = threading.Thread(
            target=parse_cmd,
            args=[command, return_list],
        )
        parse_cmd_thread.start()
        parse_cmd_thread.join()
        function_name = str(return_list[0])
        args = list(return_list[1])

        if function_name is None:
            continue
        if function_name != 'exit':
            execute_function(function_name, args)
        else:
            exit_flag = True


def parse_cmd(
    command: List[str],
    return_list: List[Any],
) -> None:
    """
    Parse command given in arguments
    :param command: str command to run
    :param return_list: for when calling in a thread, the return list is
    modified to be the return value of the function
    """
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
    args = parser.parse_args(args=command)
    return_list[0] = args.function[0]
    if args.args is not None:
        return_list[1] = args.args
    else:
        return_list[1] = []


def execute_function(function_name: str, args: List[str]):
    """
    Runs a function with the given args
    TODO: add real drop/metadata request commands that interface
    with the filesystem
    TODO: handle exceptions for real

    :param function_name: string name of the function to run
    :param args: arguments for the function to run
    """
    # for functions that create or destroy the init directory
    if function_name == "node_init":
        node_init.initialize_node(*args)
    elif function_name == "node_force_init":
        node_init.force_initialize_node(*args)
    elif function_name == "delete_node":
        node_init.delete_node_directory(*args)

    # drop functions
    elif function_name == "drop_init":
        drop_init.initialize_drop(args[0])

    elif function_name == "drop_update":
        drop_id = crypto_util.b64decode(args[0].encode())
        drop_util.update_drop(drop_id)

    elif function_name == "sync_drop":
        drop_id = crypto_util.b64decode(args[0].encode())
        # takes drop_id as b64 and save+directory
        drop_util.sync_drop(drop_id, args[1])

    else:
        print("Function [%s] not found" % (function_name))


if __name__ == '__main__':
    run_backend()
