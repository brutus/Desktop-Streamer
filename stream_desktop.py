#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Capture *audio* and *video* from the desktop and stream it to the network.

Usage:

  stream_desktop.py [-n|--gui] [-a|-A] [capture options] [stream options]

"""

from __future__ import print_function

import os
import sys
import time
import shlex
import signal
import json
import tkMessageBox
import Tkinter as tk

from subprocess import PIPE, Popen, check_output, CalledProcessError
from argparse import ArgumentParser, SUPPRESS
from collections import OrderedDict


__VERSION__ = '0.5'
__author__ = 'Brutus [DMC] <brutus.dmc@googlemail.com>'
__license__ = 'GNU General Public License v3 or above - '\
              'http://www.opensource.org/licenses/gpl-3.0.html'


class DesktopStreamerError(Exception):
  pass


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

    Using :meth:`set_settings` instead is recommended. If you do, the
    commandlines are automatically recreated on changes.

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

  def __init__(self, load=False, save=False, cfg_file=None, **settings):
    """
    Handles *settings* and creates initial commandlines.

    If *cfg_file* is set, this string is used as full path to the file
    that stores the settings. If not, the path from :attr:`CFG_FILE` is used.

    If *load* is set, the settings stored in :attr:`cfg_file` are loaded. This
    happens **after** the defaults are loaded, but **before** the additional
    *settings* are used.

    If *save* is set, the settings are saved to :attr:`cfg_file`. This happens
    **after** the additional *settings* are used.

    """
    # store save / load settings
    self.cfg_file = cfg_file if cfg_file else self.CFG_FILE
    # find commands
    self.setup_command_paths()
    # 1. load defaults
    self.set_settings(**self.SETTINGS)
    # 2. load stored settings - if wanted
    if load:
      self.load_settings()
    # 3. use additional *settings*
    self.set_settings(**settings)
    # save final settings - if wanted
    if save:
      self.save_settings()
    # create commands
    self.setup()

  def __setattr__(self, name, value):
    """
    Sets attribute *name* to *value* and handles some **special cases**.

    - If *res_in* is `None`, get the size of the whole screen.

    - If *res_out* is `None`, use same as *res_in*.

    - Cast *framerate* and *port* to `int`.

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
    Gets full paths to the used commands.

    """
    for cmd in self.COMMANDS:
      self.COMMANDS[cmd] = DesktopStreamer.get_command_path(cmd)

  def set_settings(self, **settings):
    """
    Stores *settings* as attributes.

    Call :meth:`setup` afterwards *if attributes have changed*, to reflect the
    changes in the commandlines.

    .. important::

      Only the *keys* from :attr:`SETTINGS` are used and the order is kept.

    """
    changes = False
    # process settings...
    for key in [key for key in self.SETTINGS if key in settings]:
      try:
        if settings[key] != getattr(self, key):
          setattr(self, key, settings[key])
          changes = True
      except AttributeError:
        setattr(self, key, settings[key])
        changes = True
    # create (new) commandlines on changes
    if changes:
      self.setup()

  def save_settings(self):
    """
    Save settings as JSON to :attr:`cfg_file`.

    """
    if not os.path.exists(self.cfg_file):
      os.makedirs(os.path.dirname(self.cfg_file))
    with open(self.cfg_file, 'w') as fh:
      json.dump(self.settings, fh)

  def load_settings(self):
    """
    Load settings as JSON from :attr:`cfg_file`.

    """
    try:
      with open(self.cfg_file) as fh:
        settings = json.load(fh)
      self.set_settings(**settings)
    except IOError:
      err_msg = "WARNING: Can't load settings from '{}'."
      print(err_msg.format(self.cfg_file), file=sys.stderr)

  def setup(self):
    """
    Build attr:`cmd_avconv` and attr:`cmd_vlc` commandlines from settings.

    .. note::

      If no command-path is set in :attr:`self.COMMANDS` for a command,
      the command name is used instead.

    """
    # command template: avconv
    cmd_avconv = self.COMMANDS['avconv']
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
      cmd=(cmd_avconv if cmd_avconv else 'avconv'),
      audio=(av_audio if self.audio else ''),
      video=(av_video if self.video else '')
    )
    # command template: vlc
    cmd_vlc = self.COMMANDS['cvlc']
    cmd_vlc = (
      "{cmd} "
      "-I dummy - "
      "--sout=#std{{access=http,mux=ts,dst=:{port}}}"
    ).format(
      cmd=(cmd_vlc if cmd_vlc else 'cvlc'),
      port=self.port
    )
    # build command list
    self.cmd_avconv = shlex.split(cmd_avconv, posix=False)
    self.cmd_vlc = shlex.split(cmd_vlc, posix=False)

  def start(self):
    """
    Start streaming.

    Start ``avconv`` and pipe it to ``vlc``.

    """
    # check for missing commands
    if self.missing_commands:
      msg = "The following needed commands are missing: {}."
      msg = msg.format(', '.join(self.missing_commands))
      raise DesktopStreamerError("ERROR: " + msg)
    # check if already running
    if self.running_processes:
      self.stop()
    # start...
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
    Return alist of all processes.

    """
    processes = (getattr(self, proc, None) for proc in self.PROCESSES)
    return [proc for proc in processes if proc is not None]

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

  @staticmethod
  def get_command_path(command):
    """
    Return the full path to *command* or `None` if not found.

    """
    try:
      return check_output(['which', command]).strip()
    except CalledProcessError:
      return None

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


class DSGui(tk.Frame):

  """
  Draw a TK GUI for :class:`DesktopStreamer`.

  Contains a button, that starts and stops the stream.

  """

  def __init__(self, master, streamer):
    tk.Frame.__init__(self, master)
    self.streamer = streamer
    self.return_code = 0
    self.setup_gui()

  def setup_gui(self):
    """
    Create main window and widgets.

    """
    # setup master
    self.master.title("Desktop Streamer")
    self.master.protocol("WM_DELETE_WINDOW", self.quit)
    self.grid()
    # button
    self.button = tk.Button(
      self, padx=20, pady=10, text='Start Stream',
      command=self.toggle_stream
    )
    self.button.grid_configure(padx=60, pady=20)
    self.button.grid()

  def toggle_stream(self):
    """
    Called on *button* press.

    If the stream is running stop it, else start it.

    """
    if self.button['text'] == 'Start Stream':
      try:
        self.streamer.start()
        self.button['text'] = 'Stop Stream'
      except DesktopStreamerError as err:
        self.return_code = 1
        tkMessageBox.showerror("ERROR", err)
        self.quit()
    else:
      self.streamer.stop()
      self.button['text'] = 'Start Stream'

  def quit(self):
    """
    Destroy all windows and close *streamer*.

    """
    self.streamer.stop()  # close streamer if it runs
    self.master.quit()


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


def show_gui(streamer):
  """
  Run *streamer* from GUI interface.

  """
  root = tk.Tk()
  gui = DSGui(root, streamer)
  root.mainloop()  # show GUI and wait for it to end
  return gui.return_code


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
  if gui:
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
    version=__VERSION__,
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


if __name__ == '__main__':
  sys.exit(main(**vars(_get_args())))
