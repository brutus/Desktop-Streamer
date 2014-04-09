# -*- coding: UTF-8 -*-

"""
A command line interface for :class:`desktopstreamer.DesktopStreamer`.

"""

from __future__ import absolute_import
from __future__ import print_function

import sys
import signal

from argparse import ArgumentParser, SUPPRESS

from . import DesktopStreamer, DesktopStreamerError, __version__


__all__ = ['show_cli', 'parse_arguments']


def show_cli(streamer):
  """
  Run *streamer* from CLI interface.

  """
  # register signal -> stop *streamer* on SIGINT (CTRL+C):
  signal.signal(signal.SIGINT, lambda signal, frame: streamer.stop())
  try:
    streamer.start()  # start streaming
    signal.pause()  # wait for signal
  except DesktopStreamerError as err:
    print(err, file=sys.stderr)
    return 1
  return 0


def parse_arguments(argv=None):
  """
  Return `namespace` with parsed arguments and options.

  """
  description = (
    "Capture *audio* and *video* from the desktop and stream it to the "
      "local network using `avconv` and `vlc`."
  )
  usage = (
    "\n  stream_desktop [-n|--gui] [-a|-A] [capture options] [stream options]\n"
      "  stream_desktop --version\n"
      "  stream_desktop --help"
  )
  ap = ArgumentParser(
    usage=usage,
    description=description,
    version=__version__,
    argument_default=SUPPRESS
  )
  ap_x_modes = ap.add_mutually_exclusive_group()
  ap_x_modes.add_argument(
    '-n', '--noop', action='store_true', dest='show_commands',
    help="do nothing - only print the commands"
  )
  ap_x_modes.add_argument(
    '--gui', action='store_true',
    help="show GUI"
  )
  # SETTINGS
  ag_set = ap.add_argument_group(
    "Settings",
    "Options to load and save settings. "
      "Which file is used to store them can be set with `--cgf-file`. "
      "The default is: `{}`.".format(DesktopStreamer.CFG_FILE)
  )
  ag_set.add_argument(
    '--save', action='store_true',
    help="save settings"
  )
  ag_set.add_argument(
    '--load', action='store_true',
    help="load settings"
  )
  ag_set.add_argument(
    '--cfg-file', metavar='FILENAME',
    help="full path to the config file"
  )
  # CAPTURE
  ag_cap = ap.add_argument_group(
    "Capture",
    "These options govern how the stream is being captured."
  )
  ag_x_audio = ag_cap.add_mutually_exclusive_group()
  ag_x_audio.add_argument(
    '-a', '--audio-only', action='store_false', dest='video',
    help="only capture audio (no video)"
  )
  ag_x_audio.add_argument(
    '-A', '--no-audio', action='store_false', dest='audio',
    help="don't capture audio (just video)"
  )
  ag_cap.add_argument(
    '-f', '--framerate', type=int, metavar='INT',
    help="framerate for the stream [25]"
  )
  ag_cap.add_argument(
    '-r', '--res-in', metavar='INTxINT',
    help="size of the capture area [full screen]"
  )
  ag_cap.add_argument(
    '-R', '--res-out', metavar='INTxINT',
    help="transcode to this output resolution [same as res-in]"
  )
  # STREAM
  ag_strm = ap.add_argument_group(
    "Stream",
    "These options govern how the stream is sent to the network."
  )
  ag_strm.add_argument(
    '-p', '--port', type=int,
    help="serve the stream on this port [1312]"
  )
  # return args
  return ap.parse_args()
