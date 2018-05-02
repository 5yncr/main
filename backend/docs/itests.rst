.. _itests:

itests
======

There are three itests: ``itests_simple``, ``itests_complex``, and ``itests_dht``.
All three used ``docker-compose`` to run 5yncr code in a docker container.

pre-reqs
--------
You will need docker installed and running, and your user needs permission to
run docker commands.  You will also need Linux based docker, as docker for
Windows is not yet supported.

setup
-----
In all itests, ``docker-compose`` will build the containers specified in
``itests/docker-compose.yml``, under services.  Most of these build
``itests/Dockerfile``, which installs some build dependencies and then installs
our project in /work.  It will install from your current directory, including
any uncommitted changes. The tracker is built by ``itests/Dockerfile.tracker``,
which is similar to the other Dockerfile but downloads and installs the tracker
instead.

itests-simple
-------------
``itests_simple`` just runs some simple sanity checks, from
``itests/basic_test.sh``. This mostly just checks that some important scripts run
properly.

itests-complex
--------------
This does a full end-to-end test of syncing a couple drops, using the tracker
as the drop peer store and key store.  It does ``docker-compose up -d tracker
hostnode``, which starts the tracker and ``hostnode`` in the background.  The
tracker just runs the tracker, while ``hostnode`` will download a git repo and
initialize it as a drop in /small, and a debian iso and initialize it (and
several copies of it) as a drop in /large.  It will then write the drop IDs
to ``/share/small`` and ``/share/large``, which are shared with the ``syncnode``.
It then runs the backend.

``syncnode`` is run and told to execute ``itests/syncnode.sh``, which waits for
``/share/small`` and ``/share/large`` to show up, prints the two sync commands to
``/work/itests/syncnode_debug_commands``, and then runs the backend, telling it
to look for commands in that file.

After the drops are synced, it runs the ``check_drop`` script on the two synced
drops to ensure their content is correct.

itests-dht
----------
``itests-dht`` is almost exactly the same as ``itests-complex``, except it uses the
dht as the drop peer store and key store.  It will put up ``dht_node`` and
``dht_node2`` instead of the tracker, which are simply nodes that join the dht
network.
