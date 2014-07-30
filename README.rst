================
Desktop Streamer
================

Capture *audio* and *video* from the desktop and stream it to the local
network using `avconv`_ and `vlc`_.


Python Script
=============

You can just run the python module and - if you install this package - you
could also start the provided script from the console or your desktop shell.

Usage
-----

Start the package like this ``python -m desktopstreamer [options]``. Or use
the startup script like this::

  stream_desktop [-n|--gui] [-a|-A] [capture options] [stream options]
  stream_desktop --version
  stream_desktop --help

To use it in your desktop shell, a ``.desktop`` file is provided.

Install
-------

The easiest way to install this package is trough `pip`_::

  pip install --user desktopstreamer

Or download the latest `source`_ (or get it trough ``git clone ...``) and
install it like this (from the sources root directory)::

  python setup.py install --user

Dependencies
~~~~~~~~~~~~

You don't need to install any Python dependencies.

Requirements
~~~~~~~~~~~~

`avconv`_ and `vlc`_ are required though. Install them like this:

- Debian / Ubuntu: ``sudo apt-get install libav-tools vlc``

Setup
-----

You can use the provided ``.desktop`` file and icon from the ``data/``
directory to start the script from your desktop shell.

Settings
~~~~~~~~

You can use a file to store the settings in a JSON dictionary.

The default location is ``~/.config/DesktopStreamer/settings.json``. The
supported keys are the *capture* and *stream* long-options (with ``_`` instead
of ``-``).

To store settings in this file, use the ``--save`` option. If you use it, the
current settings are stored and previous settings are overwritten. You can
create and edit it manually too.

Here's some example content:

.. code-block:: json

  {
    "port": 420,
    "res_out": "1280x720"
  }

The settings from this file are applied, if you use the ``--load`` option.

.. note::

  The provided ``.desktop`` file uses the ``--load`` option automatically each
  time.


Shell Script
============

You can source the ``data/stream_desktop.sh`` in your ``.bash_aliases`` or
similar to get a quick ``stream_desktop`` command. The python script has more
options though.


Contribute
==========

If you find any bugs, have feature ideas or similar, just use the
`issue tracker`_ on github.

Todo
----

`Taskwarrior`_ is used to maintain a list of what needs to be done. The
database is in the ``.task/`` directory.

To use it instead of your local `Taskwarrior`_ DB you have to tell the
``task`` command to use that directory. There are a couple of ways to do this:

* There is a ``.taskrc`` file in the root directory. Tell the *task* command
  to use it like this: ``task rc:.taskrc ...``.

* Or if you don't like the extra typing, point the *TASKRC* environment
  variable to it, like this: ``export TASKRC="$(pwd)/.taskrc``.


.. _avconv: http://libav.org/avconv.html
.. _vlc: http://www.videolan.org/vlc/
.. _pip: http://www.pip-installer.org/en/latest/
.. _source: https://github.com/brutus/Desktop-Streamer/archive/master.zip
.. _issue tracker: https://github.com/brutus/Desktop-Streamer/issues
.. _taskwarrior: http://taskwarrior.org/
