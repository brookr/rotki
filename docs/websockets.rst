rotki Websockets API
##################################################
.. toctree::
  :maxdepth: 2


Introduction
*************

When the rotki backend runs it exposes a websockets API that can be easily subscribed to. Through that API rotki backend pushes data to the subscribed clients (mainly the rotki frontend) in a continuous manner and as soon as they are available.


Subscribe
***********

In order to subscribe to the websockets api open a socket to the host/port combination that you have set for websockets in the backend and send an empty message.

Messages Format
*****************

All messages sent by the backend via websockets are stringified json and they have the following format.

::

    {
        "type": "legacy",
        "data": "{"some": 1, "data": 2}"
    }


The ``"type"`` attribute determines what kind of message it is and what to expect in ``"data"``.

Messages
************


Legacy messages
====================

The messages sent by rotki via the ``MessagesAggregator`` can be found in this type. The format is


::

    {
        "type": "legacy",
        "data": "{"verbosity": "warning", "value": "A warning"}"
    }


- ``verbosity``: The verbosity of the message. Can be one of ``"warning"`` or ``"error"``.
- ``value``: A string with the contents of the message.


Balance snapshot errors
=========================

The messages sent by rotki when there is a snapshot balance error. There can be multiple of these errors for one balance snapshot. The format is the following.


::

    {
        "type": "balance_snapshot_error",
        "data": "{"location": "poloniex", "error": "Could not connect to poloniex"}"
    }


- ``location``: An approximate location name for where in the balance snapshot the error happened.
- ``error``: A string with details of the error


Login status
=========================

The messages sent by rotki when a user is logging in and a db upgrade is happening. The format is the following.


::

    {
        "start_db_version": 26,
        "target_db_version": 35,
        "current_upgrade": {
            "from_db_version": 30,
            "total_steps": 8,
            "current_step": 5
        }
    }


- ``start_db_version``: DB version that user's database had before any upgrades began. This is the version of the DB when rotki first starts.
- ``current_upgrade``: Structure that holds information about currently running upgrade. Contains: `from_db_version` - version of the database that currently running upgrade is being applied to; `total_steps` - total number of steps that currently running upgrade consists of; `current_step` - step that the upgrade is at as of this websocket message. 
- ``target_db_version``: The target version of the DB. When this is reached, the upgrade process will have finished.
