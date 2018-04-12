#!/usr/bin/env python
import argparse
import json
import os

from syncr_backend.constants import DEFAULT_DPS_CONFIG_FILE
from syncr_backend.constants import DEFAULT_PKS_CONFIG_FILE
from syncr_backend.init.node_init import get_full_init_directory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ip",
        type=str,
        help='IP of the Tracker',
    )
    parser.add_argument(
        "port",
        type=int,
        help='Port of the Tracker',
    )
    args = parser.parse_args()

    config = {
        'type': 'tracker',
        'ip': args.ip,
        'port': args.port,
    }

    init_directory = get_full_init_directory(None)
    pks_config_path = os.path.join(init_directory, DEFAULT_PKS_CONFIG_FILE)
    dps_config_path = os.path.join(init_directory, DEFAULT_DPS_CONFIG_FILE)

    with open(pks_config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False)
    print("PublicKeyStore Tracker Config file created at: {}"
          .format(pks_config_path))

    with open(dps_config_path, 'w') as f:
        json.dump(config, f, ensure_ascii=False)
    print("DropPeerStore Tracker Config file created at: {}"
          .format(dps_config_path))


if __name__ == '__main__':
    main()
