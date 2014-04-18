==============
Stream Desktop
==============

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

Or download the latest `source`_ (or get it trough ``git``) and install it
like this (from the sources root directory)::

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

You can use the provided `.desktop` files to start the script from your
desktop shell.

Settings
~~~~~~~~

You can use a file to store the settings in a JSON dictionary.

The default location is ``~/.config/DesktopStreamer/settings.json``. The
supported keys are the *capture* and *stream* long-options (with ``_`` instead
of ``-``).

.. code-block:: json

  {
    "port": 420,
    "res_out": "1280x720"
  }

You can create and edit it manually. If you use the ``--save`` option, the
current settings are stored automatically (previous settings get overwritten).

The settings from this file are applied, if you use the ``--load`` option.

.. note:: The provided ``.desktop`` file uses it.


Shell Script
============

You can source the ``stream_desktop.sh`` from the `misc/` directory in your
``.bash_aliases`` or similar to get a quick ``stream_desktop`` command. The
python script has more options though.


.. _avconv: http://libav.org/avconv.html
.. _vlc: http://www.videolan.org/vlc/
.. _pip: http://www.pip-installer.org/en/latest/
.. _source: https://github.com/brutus/Desktop-Streamer/archive/master.zip
