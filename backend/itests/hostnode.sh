#!/bin/sh
set -ex -o pipefail

/work/itests/setup.sh

git clone https://github.com/yelp/paasta /small
mkdir /large
wget -v https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-9.4.0-amd64-netinst.iso -O /large/debian.iso

drop_init /small > /share/small
drop_init /large > /share/large

run_backend 0.0.0.0 2345 --external_address hostnode --backendonly
