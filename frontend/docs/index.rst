.. _index:

5yncr frontend
==============

The 5yncr frontend is simply a flask app.  It will automatically connect to the
backend if the backend is running.  All the heavy lifting happens in the
backend.

Usage
-----
After installing 5yncr-Tracker and it's dependencies, and running the backend,
do:

.. code-block:: bash

    export FLASK_APP=syncr_frontend.frontend
    flask run

Or on Windows command prompt:

.. code-block:: bat

    set FLASK_APP=syncr_frontend.frontend
    flask run

Or on PowerShell:

.. code-block:: powershell

    $env:FLASK_APP = "syncr_frontend.frontend"
    flask run

.. toctree::
    :maxdepth: 1
    :caption: API docs:

    generated/syncr_frontend


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
