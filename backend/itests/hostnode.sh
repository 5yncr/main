#!/bin/sh
set -ex -o pipefail

/work/itests/setup.sh

if [[ -d "/ext/small" ]]; then
    cp -r /ext/small /small
else
    git clone https://github.com/yelp/paasta /small
fi
mkdir /large
if [[ -f "/ext/debian.iso" ]]; then
    cp /ext/debian.iso /large/
else
    wget -v https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-9.4.0-amd64-netinst.iso -O /large/debian.iso
fi
cp /large/debian.iso /large/debian2.iso
cp /large/debian.iso /large/debian3.iso
cp /large/debian.iso /large/debian4.iso
cp /large/debian.iso /large/debian5.iso
cp /large/debian.iso /large/debian6.iso
cp /large/debian.iso /large/debian7.iso
cp /large/debian.iso /large/debian8.iso

drop_init /small > /share/small
drop_init /large > /share/large

run_backend 0.0.0.0 2345 --external_address hostnode --backendonly
