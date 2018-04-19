#!/bin/sh
set -ex -o pipefail
/work/itests/setup.sh

while [[ ! "$(cat /share/small)" ]]; do
    echo "waiting for small file..."
    sleep 5
done
while [[ ! "$(cat /share/large)" ]]; do
    echo "waiting for large file..."
    sleep 5
done

printf "sync_drop $(cat /share/small) /small;sync_drop $(cat /share/large) /large" > /work/itests/syncnode_debug_commands
run_backend 0.0.0.0 2345 --external_address $(hostname) --debug_commands /work/itests/syncnode_debug_commands


check_drop "$(cat /share/small)"
check_drop "$(cat /share/large)"
