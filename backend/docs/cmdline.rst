Command line
============

.. _check_drop:

.. autoprogram:: syncr_backend.bin.check_drop:parser()
    :prog: check_drop

.. _drop_init:

.. autoprogram:: syncr_backend.bin.drop_init:parser()
    :prog: drop_init

.. _make_dht_configs:

.. autoprogram:: syncr_backend.bin.make_dht_configs:parser()
    :prog: make_dht_configs

.. _make_tracker_configs:

.. autoprogram:: syncr_backend.bin.make_tracker_configs:parser()
    :prog: make_tracker_configs

.. _node_init:

.. autoprogram:: syncr_backend.bin.node_init:parser()
    :prog: node_init

.. warning::
    The ``--direcotry <directory>`` parameter is allowed in this script,
    but may not be recognized in other places

.. _run_backend:

.. autoprogram:: syncr_backend.bin.run_backend:parser()
    :prog: run_backend

.. note::
    It is recommended to run the backend with ``--backendonly``

.. warning::
    The ``--debug_commands`` option is not recommended unless you know what
    you're doing

.. _run_dht_server:

.. autoprogram:: syncr_backend.bin.run_dht_server:parser()
    :prog: run_dht_server

.. _sync_drop:

.. autoprogram:: syncr_backend.bin.sync_drop:parser()
    :prog: sync_drop

.. _update_drop:

.. autoprogram:: syncr_backend.bin.update_drop:parser()
    :prog: update_drop

.. note::
    Specifying ``--save-dir`` and ``--drop_id`` may have unexpected results if
    they do not match
