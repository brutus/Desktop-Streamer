#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Capture *audio* and *video* from the desktop and stream it to the network.

Usage:

  stream_desktop.py [-n|--gui] [-a|-A] [capture options] [stream options]

"""

import os
import sys
import time
import shlex
import signal
import json
import Tkinter as tk

from subprocess import PIPE, Popen, check_output, CalledProcessError
from argparse import ArgumentParser
from collections import OrderedDict


__VERSION__ = '0.3'
__author__ = 'Brutus [DMC] <brutus.dmc@googlemail.com>'
__license__ = 'GNU General Public License v3 or above - '\
              'http://www.opensource.org/licenses/gpl-3.0.html'


class DesktopStreamer(object):

  """
  Stream the desktop to the network with the ``avconv`` and ``vlc`` commands.

  The commandlines needed for those two commands are build from the arguments
  to the :meth:`__init__` method with :meth:`setup`. The final commandlines
  are stored as lists in :attr:`cmd_avconv` and :attr:`cmd_vlc`.

  You can get the commands as strings trough :attr:`cmd_avconv_as_string` and
  :attr:`cmd_vlc_as_string`.

  Use :meth:`start` to start streaming and :meth:`stop` to stop it.

  .. note::

    The attributes used to build the commandlines are set on instantiation.

    You can change them later too, but must call :meth:`setup` afterwards, or
    the commands wont reflect your change.

    Using :meth:`set` instead is recommended. If you do, the commandlines are
    automatically recreated on changes.

  """

  CFG_FILE = os.path.join(
    os.path.expanduser('~'), '.config', 'StreamDesktop', 'settings.json'
  )

  COMMANDS = OrderedDict([
    ('avconv', None),
    ('cvlc', None)
  ])

  PROCESSES = ('proc_avconv', 'proc_vlc')

  SETTINGS = OrderedDict([
    ('audio', True),
    ('video', True),
    ('res_in', None),
    ('res_out', None),
    ('framerate', 25),
    ('port', 1312)
  ])

  def __init__(self, load=False, save=None, cfg_file=None, **settings):
    """
    Store settings and create initial commandlines.

    If *cfg_file* is set, this string is used as full path to the file
    that stores the settings. If not, the file is
    ``~/.config/StreamDesktop/settings.json``.

    If *load* is set, the settings stored in *cfg_file* are loaded after the
    defaults but before the additional *settings* are set.

    If *save* is...

    - ``None``: settings are never automatically saved

    - ``False``: settings are saved automatically once after the
      additional settings are set

    - ``True``: settings are automatically saved after each change

    """
    # store save / load settings
    self.autosave = True if save else False
    if cfg_file is None:
      self.cfg_file = self.CFG_FILE
    else:
      self.cfg_file = cfg_file
    # find commands
    self.setup_command_paths()
    # set defaults
    self.set(**self.SETTINGS)
    if load:
      self.load_settings()
    # set additional settings
    self.set(**DesktopStreamer.filter_defaults(settings))
    if save is False:
      self.save_settings()
    # create commands
    self.setup()

  def __setattr__(self, name, value):
    """
    Set attribute *name* to *value* and handle some **special cases**.

    - If ``res_in`` is ``None``, get the size of the whole screen.

    - If ``res_out`` is ``None``, use same as ``res_in``.

    - Cast ``framerate`` and ``port`` to ``int``.

    """
    if name == 'res_in' and value is None:
      self.__dict__['res_in'] = DesktopStreamer.get_screensize(as_string=True)
    elif name == 'res_out' and value is None:
      self.__dict__['res_out'] = self.res_in
    elif name in ('framerate', 'port'):
      self.__dict__[name] = int(value)
    else:
      self.__dict__[name] = value

  def setup_command_paths(self):
    """
    Get full paths to the used commands.

    """
    for cmd in self.COMMANDS:
      self.COMMANDS[cmd] = DesktopStreamer.get_command_path(cmd)

  def set(self, **settings):
    """
    Store *settings* as attributes.

    Call :meth:`setup` afterwards *if attributes have changed*, to reflect the
    changes in the commandlines.

    If :attr:`autosave` is set, settings are saved with :meth:`save_settings`
    after a call that *changed the settings*.

    .. important::

      Only the *keys* from :attr:`SETTINGS` are used and the order is kept.

    """
    changes = False
    for key in [key for key in self.SETTINGS if key in settings]:
      try:
        if settings[key] != getattr(self, key):
          setattr(self, key, settings[key])
          changes = True
      except AttributeError:
        setattr(self, key, settings[key])
        changes = True
    if changes:
      self.setup()  # create commands
      if self.autosave:
        self.save_settings()

  def save_settings(self):
    """
    Save settings as JSON to :attr:`cfg_file`.

    """
    if not os.path.exists(self.cfg_file):
      path = os.path.dirname(self.cfg_file)
      os.makedirs(path)
    with open(self.cfg_file, 'w') as fh:
      json.dump(self.settings, fh)

  def load_settings(self):
    """
    Load settings as JSON from :attr:`cfg_file`.

    """
    if os.path.exists(self.cfg_file):
      with open(self.cfg_file) as fh:
        settings = json.load(fh)
      autosave, self.autosave = self.autosave, False
      self.set(**settings)
      self.autosave = autosave

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
      "{cmd} {audio} {video} -threads 0 -f mpegts -"
    ).format(
      cmd=self.COMMANDS['avconv'],
      audio=(av_audio if self.audio else ''),
      video=(av_video if self.video else '')
    )
    cmd_vlc = (
      "{cmd} "
      "-I dummy - "
      "--sout=#std{{access=http,mux=ts,dst=:{port}}}"
    ).format(
      cmd=self.COMMANDS['cvlc'],
      port=self.port
    )
    # build command list
    self.cmd_avconv = shlex.split(cmd_avconv, posix=False)
    self.cmd_vlc = shlex.split(cmd_vlc, posix=False)

  def start(self):
    """
    Start streaming.

    Start `avconv` and pipe it to `cvlv`.

    """
    if self.running_processes:
      self.stop()
    self.proc_avconv = Popen(self.cmd_avconv, stdout=PIPE)
    self.proc_vlc = Popen(
      self.cmd_vlc, stdin=self.proc_avconv.stdout, stdout=PIPE
    )
    self.proc_avconv.stdout.close()

  def stop(self, seconds=2):
    """
    Stop streaming.

    Stop all running processes.

    """
    terminated = False
    while self.running_processes:
      if terminated:
        map(lambda proc: proc.kill(), self.running_processes)
      else:
        map(lambda proc: proc.terminate(), self.running_processes)
        terminated = True
      time.sleep(seconds)  # give them some time...

  @property
  def settings(self):
    """
    Return a dictionary containing all settings.

    """
    return {k: v for k, v in self.__dict__.items() if k in self.SETTINGS}

  @property
  def settings_as_json(self):
    """
    Return a dictionary containing all settings as JSON string.

    """
    return json.dumps(self.settings)

  @property
  def cmd_avconv_as_string(self):
    """
    Return the `avconv` command as string.

    """
    return " ".join(self.cmd_avconv)

  @property
  def cmd_vlc_as_string(self):
    """
    Return the `cvlc` command as string.

    """
    return " ".join(self.cmd_vlc)

  @property
  def processes(self):
    """
    Return a list of all processes.

    """
    return filter(
      lambda proc: proc is not None,
      [getattr(self, proc, None) for proc in self.PROCESSES]
    )

  @property
  def running_processes(self):
    """
    Return a list of all running processes.

    """
    return [proc for proc in self.processes if proc.poll() is None]

  @property
  def missing_commands(self):
    """
    Return a list of missing commands.

    """
    return [cmd for cmd in self.COMMANDS if self.COMMANDS[cmd] is None]

  @property
  def missing_commands_as_string(self):
    """
    Return the missing commands as a string.

    """
    if self.missing_commands:
      return "The following needed commands are missing: {}.\n".format(
        ', '.join(self.missing_commands)
      )
    else:
      return "No needed commands are missing."

  @staticmethod
  def get_command_path(command):
    """
    Return the full path to the *command*.

    """
    try:
      return check_output(['which', command]).strip()
    except CalledProcessError:
      return None

  @staticmethod
  def filter_defaults(args):
    """
    Return a new dictionary based on *args* conatinig only those key
    that are not present in :attr:`SETTINGS` or got different values.

    """
    return {
      k: v for k, v in args.items() if
        k not in DesktopStreamer.SETTINGS or v != DesktopStreamer.SETTINGS[k]
    }

  @staticmethod
  def get_screensize(as_string=False):
    """
    Return screen size as *width*, *height* tuple.

    Or as a ``<width>x<height>`` string if *as_string* is set.

    """
    root = tk.Tk()  # get root window
    root.withdraw()  # but don't show it
    width, height = root.winfo_screenwidth(), root.winfo_screenheight()
    return "{}x{}".format(width, height) if as_string else (width, height)


def show_cli(streamer):
  """
  Run *streamer* from CLI interface.

  """
  if streamer.missing_commands:
    print(streamer.missing_commands_as_string)
    return 1
  # register signal -> stop *streamer* on SIGINT (CTRL+C):
  signal.signal(signal.SIGINT, lambda signal, frame: streamer.stop())
  streamer.start()  # start streaming
  signal.pause()  # wait for signal
  return 0


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

  :param cmd_options: arguments for :class:`DesktopStreamer`.

  """
  streamer = DesktopStreamer(**cmd_options)
  if show_commands:
    print(streamer.cmd_avconv_as_string)
    print(streamer.cmd_vlc_as_string)
    return 0
  elif gui:
    return show_gui(streamer)
  else:
    return show_cli(streamer)


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
  # SETTINGS
  ag_set = ap.add_argument_group('Settings')
  ag_set.add_argument(
    '-s', '--save', action='store_false',
    help="save settings"
  )
  ag_set.add_argument(
    '-l', '--load', action='store_true',
    help="load settings"
  )
  ag_set.add_argument(
    '-F', '--cfg-file',
    help="full path to config file"
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
    save=None,
    audio=True,
    video=True,
    framerate=25,
    port=1312
  )
  # return args
  return ap.parse_args()


if __name__ == '__main__':
  sys.exit(main(**vars(_get_args())))
