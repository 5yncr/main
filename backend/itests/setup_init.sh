#!/bin/sh
set -ex -o pipefail

node_init

echo "USE_DHT $USE_DHT"

if [[ -z "${USE_DHT}" ]]
then
  make_tracker_configs tracker 2346
else
  make_dht_configs 2345
fi
