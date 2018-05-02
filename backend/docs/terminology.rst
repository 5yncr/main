.. _terms:

Terminology
===========

This document describes the 5yncr specific vocabulary.


Drop
----
A "drop" is the basic unit of syncing in 5yncr.  It is a directory and all the
files and folders within it (recursively).  The contents of a drop may be
shared with other users by giving them a "drop id", which is a random string
that uniquely identifies the drop.  Drops may be updated by the primary or
secondary owners (see owner_).

Subscribe
---------
The act of downloading a drop is called "subscribing".  It is called this since
it also means receiving updates to the drop later.

Owner
-----
Drop permissions are split in three: the primary owner, zero or more secondary
owners, and everyone else.  The primary owner has ultimate control, and may
make changes or change secondary owners.  The secondary owners may only change
the drop contents.  Everyone else may subscribe to the drop, but not modify it.

Primary ownership transfer is a planned feature.

.. _dps:

DPS
---
"DPS" stands for "drop peer store".  It is an abstract place that stores the
mapping between a drop and every node that claims to be subscribed to it.

.. _pks:

Public Key Store
----------------
A public key store (sometimes key store, or PKS) acts as a public key server
for nodes.  Nodes can ask the key store for a public key to validate drop
changes.  Node IDs are simply the hash of public keys, so it's not possible to
send a key store a fake public key for a node.

Tracker
-------
A tracker is a centralized implementation of a DPS and Public Key Store.  It is
accessed over TCP, and support is built into 5yncr.

The reference tracker is currently the recommended key store and DPS.

DHT
---
The DHT is an experimental decentralized DPS and Public Key Store.  It is a
modified kademlia distributed hash table that stores the same information as a
tracker.  The current implementation may change dramatically before release.
