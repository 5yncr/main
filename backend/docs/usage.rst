.. _usage:

Usage
=====

This document describes the command line usage of 5yncr.  For using via the
frontend, please see :ref:`the frontend docs <frontend:index>`.

One time node initialization
----------------------------
Before first use, a user must initialize their node.  This creates the
necessary directories [#]_ and key-pair.

Initialize a node with :ref:`node_init <node_init>`.

.. [#] Usually ~/.5yncr and subdirectories

Drop initialization
----------------------------
On the backend, a drop can be initialized (created) with the :ref:`drop_init
<drop_init>` script.  It takes the directory to initialize as a parameter, and
outputs the drop ID encoded with base64, which is used to a sync the drop on
other nodes.

Creating DPS and Key Store configs
----------------------------------
Before running the backend, :ref:`dps` and :ref:`pks` configs are required.
These are created with :ref:`make_tracker_configs <make_tracker_configs>` or
:ref:`make_dht_configs <make_dht_configs>`, for using a tracker or DHT,
respectively.

To use the tracker, run ``make_tracker_configs IP PORT``, where ``IP`` and
``PORT`` are the ip and port of a tracker.

To use the DHT, run ``make_dht_configs --bootstrap-peers
ip1:port1,ip2:port2,...  listenport`` where ``ip1:port1`` and ``ip2:port2`` are
existing DHT nodes to bootstrap from and ``listenport`` is the port the DHT will
listen on when running as part of the backend.

Currently only using one tracker or the DHT is supported.  A tracker is
recommended.

Running the backend
-------------------
Once the node is initialized, a drop is created, and DPS/KeyStore configs are
made, :ref:`run_backend <run_backend>` will start the node listening for
incoming requests.

The backend should be run as ``run_backend --backendonly ip port``.  Specifying
``--backendonly`` is recommended unless you know what you're doing, and
``--debug_commands`` should only be used if you know what you're doing.  ``ip``
and ``port`` are the local ip and port to bind to.  If those are different than
where the node can be reached from other nodes, specify ``--external_address
address`` and/or ``--external_port port``.

The recommended commend to run the backend is ``run_backend --backendonly
--external_address example.com 0.0.0.0 random_port``.  This will likely be
simplified in the future.

Adding other users' drops
-------------------------
On the backend, the :ref:`sync_drop <sync_drop>` command subscribes to other
nodes' drops.  It takes two arguments: ``drop_id`` and ``directory``.  For
example, ``sync_drop reallylongbase64string /home/username/a/directory``.

This requires a tracker/dht config file to exist, and will run until the drop
is fully synced.

Updating drops you own with new files
-------------------------------------
The :ref:`update_drop <update_drop>` script updates an owned drop.  It takes
either ``--save_dir directory`` or ``--drop_id dropid``.

Specifying both is possible, but may lead to unexpected results if the
specified directory does not match the drop_id.

Downloading updates from other users
------------------------------------
(TODO: figure out how to do this)
