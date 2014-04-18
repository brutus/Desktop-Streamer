#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
A class to capture *audio* and *video* from the desktop and stream it to the
network.

The external ``avconv`` and ``vlc`` commands are used for this.

"""

from __future__ import absolute_import
from __future__ import print_function

import os
import sys
import time
import shlex
import json
import Tkinter as tk

from subprocess import PIPE, Popen, check_output, CalledProcessError
from collections import OrderedDict

from . import DesktopStreamerError


__all__ = ['DesktopStreamer']


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
    os.path.expanduser('~'), '.config', 'DesktopStreamer', 'settings.json'
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
