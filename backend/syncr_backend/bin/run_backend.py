#!/usr/bin/env python
import argparse
import asyncio
import threading
from typing import List

from syncr_backend.external_interface.dht_util import initialize_dht
from syncr_backend.external_interface.drop_peer_store import send_drops_to_dps
from syncr_backend.init import drop_init
from syncr_backend.init import node_init
from syncr_backend.metadata.drop_metadata import send_my_pub_key
from syncr_backend.network.handle_frontend import setup_frontend_server
from syncr_backend.network.listen_requests import start_listen_server
from syncr_backend.util import crypto_util
from syncr_backend.util import drop_util
from syncr_backend.util.fileio_util import load_config_file
from syncr_backend.util.log_util import get_logger
# from syncr_backend.network import send_requests
logger = get_logger(__name__)


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
    input_args_parser.add_argument(
        "--external_address",
        type=str,
        help="Set this if the external address is different from the listen "
        "address",
    )
    input_args_parser.add_argument(
        "--external_port",
        type=int,
        help="Set this if the external port is different from the listen port",
    )
    input_args_parser.add_argument(
        "--debug_commands",
        type=str,
        help="Command file to send debug commands",
    )
    arguments = input_args_parser.parse_args()
    if arguments.external_address is not None:
        ext_addr = arguments.external_address
    else:
        ext_addr = arguments.ip[0]
    if arguments.external_port is not None:
        ext_port = arguments.ext_port
    else:
        ext_port = int(arguments.port[0])

    loop = asyncio.get_event_loop()

    # initilize dht
    config_file = loop.run_until_complete(load_config_file())
    if config_file['type'] == 'dht':
        ip_port_list = list(
            zip(
                config_file['bootstrap_ips'],
                config_file['bootstrap_ports'],
            ),
        )
        initialize_dht(ip_port_list, config_file['listen_port'])

    loop.create_task(send_my_pub_key())

    shutdown_flag = threading.Event()
    listen_server = loop.run_until_complete(
        start_listen_server(arguments.ip[0], arguments.port[0]),
    )
    frontend_server = loop.run_until_complete(
        setup_frontend_server(),
    )
    dps_send = loop.create_task(
        send_drops_to_dps(ext_addr, ext_port, shutdown_flag),
    )

    if not arguments.backendonly:
        if arguments.debug_commands is None:
            print("Not implemented")
        else:
            t = threading.Thread(
                target=run_debug_commands,
                args=[arguments.debug_commands, loop],
            )
            t.start()
    try:
        loop.run_forever()
    finally:
        shutdown_flag.set()
        listen_server.close()
        frontend_server.close()
        dps_send.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        loop.close()


def run_debug_commands(
    commands_file: str, loop: asyncio.AbstractEventLoop,
) -> None:
    """
    Read and execute commands a list of semicolon separated commands as input

    :param commands: list of semicolon separated commands
    """
    with open(commands_file) as f:
        commands = f.read().replace('\n', '')

    commandlist = commands.split(';')
    for command in commandlist:

        args = command.split(' ')
        logger.info("Ran Command %s", args)
        execute_function(args[0], args[1:], loop)

    loop.stop()


def execute_function(
    function_name: str, args: List[str], loop: asyncio.AbstractEventLoop,
) -> None:
    """
    Runs a function with the given args

    :param function_name: string name of the function to run
    :param args: arguments for the function to run
    """
    # TODO: add real drop/metadata request commands that interface
    #  with the filesystem
    # TODO: handle exceptions for real
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
        task = asyncio.run_coroutine_threadsafe(
            drop_util.update_drop(drop_id),
            loop,
        )
        task.result()
        # loop.call_soon_threadsafe(task)
        # while not task.done():
        #     time.sleep(10)

    elif function_name == "sync_drop":
        drop_id = crypto_util.b64decode(args[0].encode())
        # takes drop_id as b64 and save+directory

        async def sync_wrapper(drop_id: bytes, save_dir: str) -> None:

            await drop_util.sync_drop(drop_id, save_dir)

        task = asyncio.run_coroutine_threadsafe(
            sync_wrapper(drop_id, args[1]),
            loop,
        )
        task.result()

    else:
        print("Function [%s] not found" % (function_name))


if __name__ == '__main__':
    run_backend()
