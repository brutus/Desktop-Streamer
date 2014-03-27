#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Capture *audio* and *video* from the desktop and stream it to the network.

Usage:

  stream_desktop.py [-n|--gui] [-a|-A] [capture options] [stream options]

"""

import sys
import time
import shlex
import signal
import Tkinter as tk

from subprocess import PIPE, Popen
from argparse import ArgumentParser


__VERSION__ = '0.2'
__author__ = 'Brutus [DMC] <brutus.dmc@googlemail.com>'
__license__ = 'GNU General Public License v3 or above - '\
              'http://www.opensource.org/licenses/gpl-3.0.html'


class DeskStreamer(object):

  """
  Stream the desktop to the network with the ``avconv`` and ``vlc`` commands.

  The commandlines needed for those two commands are build from the arguments
  to the :meth:`__init__` method with :meth:`setup`. The final commandlines
  are stored as lists in :attr:`cmd_avconv` and :attr:`cmd_vlc`.

  You can get the commands as strings trough :attr:`cmd_avconv_as_string` and
  :attr:`cmd_vlc_as_string`.

  Use :meth:`start` to start streaming and :meth:`stop` to stop it.

  .. note::

    The attributes used to build the commandlines are set on instanciation.

    You can change them later too, but must call :meth:`setup` afterwards, or
    the commands wont reflect your change.

  """

  def __init__(
    self, audio=True, video=True,
    framerate=25, res_in=None, res_out=None,
    port=1312
  ):
    self.audio = bool(audio)
    self.video = bool(video)
    self.framerate = int(framerate)
    self.res_in = res_in if res_in else DeskStreamer.get_screensize(
      as_string=True
    )
    self.res_out = res_out if res_out else self.res_in
    self.port = int(port)
    self.setup()

  def setup(self):
    """
    Build *cmd_avconv* and *cmd_vlc* commandlines from settings.

    """
    # command templates
    av_audio = (
      "-f alsa -ac 2 -i pulse -acodec libmp3lame"
    )
    av_video = (
      "-f x11grab -r {framerate} -s {res_in} -i :0.0 "
      "-vcodec libx264 -preset ultrafast -s {res_out}"
    ).format(
      framerate=self.framerate, res_in=self.res_in, res_out=self.res_out
    )
    cmd_avconv = (
      "avconv {audio} {video} -threads 0 -f mpegts -"
    ).format(
      audio=(av_audio if self.audio else ''),
      video=(av_video if self.video else '')
    )
    cmd_vlc = (
      "cvlc "
      " -I dummy - "
      "--sout='#std{{access=http,mux=ts,dst=:{port}}}'"
    ).format(
      port=self.port
    )
    # build command list
    self.cmd_avconv = shlex.split(cmd_avconv, posix=False)
    self.cmd_vlc = shlex.split(cmd_vlc, posix=False)

  def start(self):
    self.proc_avconv = Popen(self.cmd_avconv, stdout=PIPE)
    self.proc_vlc = Popen(self.cmd_vlc, stdin=self.proc_avconv.stdout, stdout=PIPE)
    self.proc_avconv.stdout.close()

  def stop(self, seconds=2):
    processes = ('proc_avconv', 'proc_vlc')
    terminated = False
    # terminate created processes:
    processes = filter(None, [getattr(self, proc) for proc in processes])
    while processes:
      # stop those still running:
      if terminated:
        map(lambda proc: proc.kill(), processes)
      else:
        map(lambda proc: proc.terminate(), processes)
        terminated = True
      time.sleep(seconds)  # give them some time...
      # keep those that are still running
      processes = [proc for proc in processes if proc.poll() is None]

  @property
  def cmd_avconv_as_string(self):
    return " ".join(self.cmd_avconv)

  @property
  def cmd_vlc_as_string(self):
    return " ".join(self.cmd_vlc)

  @staticmethod
  def get_screensize(as_string=False):
    """
    Return screensize as *width*, *height* tuple.

    Or as a `<width>x<height>` string if *as_string* is set.

    """
    root = tk.Tk()  # get root window
    root.withdraw()  # but don't show it
    width, height = root.winfo_screenwidth(), root.winfo_screenheight()
    return "{}x{}".format(width, height) if as_string else (width, height)


def show_cli(streamer):
  """
  Run *streamer* from CLI interface.

  """
  # register signal: stop *streamer* on SIGINT
  signal.signal(signal.SIGINT, lambda signal, frame: streamer.stop())
  streamer.start()  # start streaming
  signal.pause()  # sleep till signal


def show_gui(streamer):
  """
  Run *streamer* from GUI interface.

  """
  def _toggle_stream(button, streamer):
    """
    Toggle *button* text and *streamer* state.

    """
    if button['text'] == 'Start Stream':
      streamer.start()
      button['text'] = 'Stop Stream'
    else:
      streamer.stop()
      button['text'] = 'Start Stream'
  root = tk.Tk()
  root.title("Desktop Streamer")
  button = tk.Button(
    root, padx=20, pady=10, text='Start Stream',
    command=lambda: _toggle_stream(button, streamer)
  )
  button.grid_configure(padx=60, pady=20)
  button.grid()
  root.mainloop()


def main(show_commands=False, gui=False, **cmd_options):
  """
  Format commands according to *cmd_options* and run them.

  If *show_commands* is set, only print the commands, don't run them.
  If *gui* is set, show a window too start and stop the stream.

  :param cmd_options: arguments for :class:`DeskStreamer`.

  """
  streamer = DeskStreamer(**cmd_options)
  if show_commands:
    print(streamer.cmd_avconv_as_string)
    print(streamer.cmd_vlc_as_string)
  elif gui:
    show_gui(streamer)
  else:
    show_cli(streamer)
  return 0


def _get_args(argv=None):
  """
  Return `namespace` with parsed arguments and options.

  """
  ap = ArgumentParser(
    usage='\n' + __doc__.split('\n\n')[-2],
    description=__doc__.split('\n\n')[0],
    version=__VERSION__
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
  # CAPTURE
  ag_cap = ap.add_argument_group('Capture')
  ag_x_audio = ag_cap.add_mutually_exclusive_group()
  ag_x_audio.add_argument(
    '-a', '--audio-only', action='store_false', dest='video',
    help="only capture audio"
  )
  ag_x_audio.add_argument(
    '-A', '--no-audio', action='store_false', dest='audio',
    help="don't capture audio"
  )
  ag_cap.add_argument(
    '-f', '--framerate', type=int, metavar='INT',
    help="the framerate to use for the stream [25]"
  )
  ag_cap.add_argument(
    '-r', '--res-in', metavar='INTxINT',
    help="the size of the capture area [full screen]"
  )
  ag_cap.add_argument(
    '-R', '--res-out', metavar='INTxINT',
    help="transcode to this output resolution [same as res-in]"
  )
  # STREAM
  ag_strm = ap.add_argument_group('Stream')
  ag_strm.add_argument(
    '-p', '--port', type=int,
    help="serve the stream on this port [1312]"
  )
  # defaults
  ap.set_defaults(
    audio=True,
    video=True,
    framerate=25,
    port=1312
  )
  # return args
  return ap.parse_args()


if __name__ == '__main__':
  sys.exit(main(**vars(_get_args())))
