#!/bin/sh
set -ex -o pipefail

run_backend -h

node_init

drop_init /work
