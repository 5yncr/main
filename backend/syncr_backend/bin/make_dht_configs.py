#!/usr/bin/env python
import argparse
import json
import os
from typing import List  # NOQA

from syncr_backend.constants import DEFAULT_DPS_CONFIG_FILE
from syncr_backend.constants import DEFAULT_PKS_CONFIG_FILE
from syncr_backend.init.node_init import get_full_init_directory
from syncr_backend.util.log_util import get_logger


logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "listenport",
        type=int,
        help='Port to listen on for DHT',
        default="",
    )
    parser.add_argument(
        "--bootstrap-peers",
        type=str,
        help=(
            'Peers of the DHT bootstrap.\n'
            'Usage: --bootstrap-peers ip:port,ip2:port2,...'
        ),
    )
    args = parser.parse_args()

    iplist = []  # type: List[str]
    portlist = []  # type: List[int]
    if args.bootstrap_peers is not None:
        peerlist = args.bootstrap_peers.split(',')
        try:
            iplist = list(map(lambda x: x.split(':')[0], peerlist))

            portlist = list(map(lambda x: int(x.split(':')[1]), peerlist))

        except IndexError:
            print("Must have at least 1 bootstrap ip")
            exit(1)

    config = {
        'type': 'dht',
        'bootstrap_ips': iplist,
        'bootstrap_ports': portlist,
        'listen_port': args.listenport,
    }
    logger.info("Created DHT config file")
    init_directory = get_full_init_directory(None)
    pks_config_path = os.path.join(init_directory, DEFAULT_PKS_CONFIG_FILE)
    dps_config_path = os.path.join(init_directory, DEFAULT_DPS_CONFIG_FILE)

    with open(pks_config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False)
    print("PublicKeyStore DHT Config file created at: {}"
          .format(pks_config_path))

    with open(dps_config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False)
    print("DropPeerStore DHT Config file created at: {}"
          .format(dps_config_path))


if __name__ == '__main__':
    main()
