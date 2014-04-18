#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Contains some function to make the package run-able.

These are also used by the start-skript - ``stream_desktop`` - which is
created if this this package is installed.

"""

from __future__ import absolute_import
from __future__ import print_function

import sys

from . import DesktopStreamer, show_gui, show_cli, parse_arguments


__all__ = ['run', 'main']


def run(show_commands=False, gui=False, **cmd_options):
  """
  Create the needed commands according to *cmd_options* and run them.

  If *show_commands* is set, only print the commands, don't run them.
  If *gui* is set, show a window to start and stop the stream.

  :param cmd_options: arguments for :class:`desktopstreamer.DesktopStreamer`.

  """
  streamer = DesktopStreamer(**cmd_options)
  if show_commands:
    print(streamer.cmd_avconv_as_string)
    print(streamer.cmd_vlc_as_string)
    return 0
  if gui:
    return show_gui(streamer)
  else:
    return show_cli(streamer)


def main(argv=None):
  """
  Starts the app with :meth:`run` and returns its *return value*.

  Parses the options for :meth:`run` with :func:`get_args`. If *argv* is
  supplied, it is used as commandline, else the actual one is used.

  """
  return run(**vars(parse_arguments(argv)))


if __name__ == '__main__':
  sys.exit(main())
