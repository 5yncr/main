#!/bin/sh
set -ex -o pipefail
/work/itests/setup.sh

while [[ ! $(cat /share/small) ]]; do
    echo "waiting for small file..."
    sleep 5
done
while [[ ! $(cat /share/large) ]]; do
    echo "waiting for large file..."
    sleep 5
done

sync_drop $(cat /share/small) /small | grep "Drop successfully synced"
sync_drop $(cat /share/large) /large | grep "Drop successfully synced"
