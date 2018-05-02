.. 5yncr documentation master file, created by
   sphinx-quickstart on Thu Apr 26 21:46:39 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to 5yncr's documentation!
=================================

5yncr is a distributed, peer-to-peer file synchronization and distribution
program.  "Drops" are synced in a peer-to-peer manner similar to bittorrent,
but may also be updated by the original creator or designated secondary owners.

5yncr's Python implementation is currently **alpha** software.  The protocol
and file formats are likely to change in backward incompatible ways without
warning, and the only supported method of running is by pulling all the repos
from github and running it manually.  The Python implementation is designed as
a reference implementation, but currently also defines the protocol
specification.  Before beta, the spec will be frozen and published.

5yncr currently has three components: backend, frontend, and tracker.  The
backend does all the heavy lifting: creating, syncing, and updating drops;
making and responding to network requests; and calculating information to be
sent to the frontend.  The frontend is simply a flask app that creates a UI to
be used in a web browser.  It communicates over a network or unix socket to the
backend.  The tracker is similar to a tracker in bittorrent: it keeps track of
which nodes are syncing which drops, and acts as a key server for public keys.
See :ref:`the tracker docs <tracker:index>` for documentation on running the
tracker.  See :ref:`the frontend docs <frontend:index>` for documentation on
running the frontend.  Read on for how to use the backend.

Before continuing, please look through the :ref:`terms`.  Then, continue to
:ref:`usage` for instructions on using 5yncr from the command line.

.. toctree::
  :maxdepth: 1
  :caption: Documentation:

  usage
  cmdline
  terminology
  itests
  asyncio

.. toctree::
   :maxdepth: 1
   :caption: API docs:

   generated/syncr_backend


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
