# -*- coding: UTF-8 -*-

"""
Capture *audio* and *video* from the desktop and stream it to the network.

You can run this package like this:

  python -m desktopstreamer [-n|--gui] [-a|-A] [capture options] [stream options]

Or use the provided start script called ``stream_desktop`` if you installed
this package. If you installed this package, you could also run this from
your desktop shell under the name *Desktop Streamer*.

"""

from __future__ import absolute_import


__all__ = [
  'DesktopStreamer', 'DesktopStreamerError', 'DSGui',
  'parse_arguments', 'show_cli', 'show_gui'
]

__version__ = '0.7'
__author__ = 'Brutus [DMC] <brutus.dmc@googlemail.com>'
__license__ = 'GNU General Public License v3 or above - '\
              'http://www.opensource.org/licenses/gpl-3.0.html'


class DesktopStreamerError(Exception):
  pass


from .desktopstreamer import DesktopStreamer
from .cli import parse_arguments, show_cli
from .gui import DSGui, show_gui
from .__main__ import run, main
