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

User Manual
===========

The following is a brief manual outlining the functionalities of the flask
app.

Sidebar
-------

The sidebar consists of two sections: **Owned Drops** and
**Subscribed Drops**. Each section contains a list of
drops that the user owns or are subscribed to, respectively.

Click on any of the drops in the sidebar to view their contents.

Owner Buttons
-------------

- **Update Drop to the Current Version**

    The *Version* button will only appear if the drop has
    been modified. That being said, clicking the button will
    update the drop and its metadata information to

- **View and Manage other Owners**

    The *Owners* button displays all current owners of the
    drop. By clicking it, the main UI panel updates to
    show both primary and secondary owners. The primary owner
    cannot be removed from the drop, but secondary owners can.
    To do so, click the *remove* button to the right of the
    corresponding owner.

    **[Insert image here that displays owners]**

Subscriber Buttons
------------------

- **Unsubscribe from the Current Drop**

    The *Unsubscribe* button makes it so that a user no longer
    receives updates to a drop. The drop directory does **not**
    get deleted, and its version is the most recently downloaded
    version prior to unsubscribing.

    **[Insert images as needed]**

General User Buttons
--------------------

- **Share the Node ID**

    The *Share* button is available for both owned and
    subscribed drops. Clicking it will update the main
    UI panel, displaying the drop's unique Drop ID.

    5yncr does not provide any utilities to message
    between individuals. In order to send the Drop ID
    to peers, you must do so through email / word of
    mouth / etc.

    **[Insert image of sharing ID example]**

- **Create a Drop**

    The *Create Drop* button is available upon opening
    the 5yncr webpage, and is located next to the **5yncr**
    title. To create a drop, do the following:

    1) Create a directory that will house the drop. Remember
    the file path.

    2) Click on *Create Drop*. The main UI panel will display
    directories on your computer.

    3) Click on the directories until the file path at the top
    of the main UI panel is the same as the file path before.

    4) Click the *Create Drop Here* button.

    **[Insert images as needed]**

- **Subscribe to a Drop**

    The *Subscribe Drop* button is available upon opening
    the 5yncr webpage, and is located next to the **5yncr**
    title. To subscribe to a drop, do the following:

    1) Create a directory that will house the drop. Remember
    the file path.

    2) Click on *Subscribe to Drop*. The main UI panel will display
    directories on your computer.

    3) Click on the directories until the file path at the top
    of the main UI panel is the same as the file path before.

    4) Input the Drop ID in the text field at the top of the main
    UI panel

    5) Click the *Subscribe* button.

    **[Insert images as needed]**

- **Delete the Drop**

    The *Delete Drop* button is available for both owned and
    subscribed drops. Clicking it will result in an alert appearing.
    Clicking 'Yes' on the alert will delete the drop directory and
    all of its contents from your computer.

    **[Insert images as needed]**

- **Redirect to the Main Webpage**

    To redirect to the main webpage, click the **5yncr** title.

    **[Insert images as needed]**


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
