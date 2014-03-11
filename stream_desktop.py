#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Capture *audio* and *video* from desktop and stream it to the local network.

Usage:
  stream_desktop.py [-n|--gui] [-a|-A] [options]

Options:
 -n, --show-commands  don't do anything, just show the commands
 --gui  show a GUI to start and stop the stream
 -a, --audio-only  only export audio
 -A, --no-audio  don't export audio
 -f <INT>, --framerate=<INT>  the framerate to use for the stream [default: 25]
 -r <WIDTHxHIGHT>, --res-in=<WIDTHxHIGHT>  the size of the capture area [default: 1920x1080]
 -R <WIDTHxHIGHT>, --res-out=<WIDTHxHIGHT>  transcode to this output resolution [default: 1280x720]
 -p <INT>, --port=<INT>  serv the stream on this port on all devices [default: 1312]

"""

import sys
import time
import shlex
import signal
import Tkinter as tk

import docopt

from subprocess import PIPE, Popen


__VERSION__ = '0.2'


class DeskStreamer(object):

  def __init__(
    self, use_audio=True, use_video=True,
    framerate=25, res_in=None, res_out=None,
    port=1312
  ):
    self.use_audio = bool(use_audio)
    self.use_video = bool(use_video)
    self.framerate = int(framerate)
    self.res_in = res_in if res_in else DeskStreamer.get_screensize()
    self.res_out = res_out if res_out else self.res_in
    self.port = int(port)
    # build commands
    self.cmd_av, self.cmd_vlc = DeskStreamer.build_commands(
      self.use_audio, self.use_video,
      self.framerate, self.res_in, self.res_out,
      self.port
    )

  def start(self):
    self.proc_av = Popen(self.cmd_av, stdout=PIPE)
    self.proc_vlc = Popen(self.cmd_vlc, stdin=self.proc_av.stdout, stdout=PIPE)
    self.proc_av.stdout.close()

  def stop(self, seconds=2):
    self.proc_av.terminate()
    self.proc_vlc.terminate()
    time.sleep(seconds)
    while self.proc_av.poll() is None or self.proc_vlc.poll() is None:
      if self.proc_av.poll() is None:
        self.proc_av.kill()
      if self.proc_vlc.poll() is None:
        self.proc_vlc.kill()
      time.sleep(seconds)

  @property
  def cmd_str_av(self):
    return " ".join(self.cmd_av)

  @property
  def cmd_str_vlc(self):
    return " ".join(self.cmd_vlc)

  @property
  def returncode(self):
    return self.proc_vlc.returncode

  @staticmethod
  def build_commands(
    use_audio, use_video,
    framerate, res_in, res_out,
    port
  ):
    """
    Return tuple of formated `avconv` and `vlc` commandlines, each as a list.

    """
    # command templates
    av_audio = (
      "-f alsa -ac 2 -i pulse -acodec libmp3lame"
    )
    av_video = (
      "-f x11grab -r {framerate} -s {res_in} -i :0.0 "
      "-vcodec libx264 -preset ultrafast -s {res_out}"
    ).format(
      framerate=framerate, res_in=res_in, res_out=res_out
    )
    cmd_av = (
      "avconv {audio} {video} -threads 0 -f mpegts -"
    ).format(
      audio=(av_audio if use_audio else ''),
      video=(av_video if use_video else ''),
    )
    cmd_vlc = (
      "cvlc "
      " -I dummy - "
      "--sout=#std{{access=http,mux=ts,dst=:{port}}}"
    ).format(
      port=port
    )
    # build command list
    return (
      shlex.split(cmd_av, posix=False),
      shlex.split(cmd_vlc, posix=False)
    )

  @staticmethod
  def get_screensize(as_string=True):
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
  Run *streamer* in CLI interface.

  """
  def _raise_ki_on_signal(signal, frame):
    """
    Catch signal and raise a *KeyboardInterrupt*.

    """
    raise KeyboardInterrupt
  try:
    signal.signal(signal.SIGINT, _raise_ki_on_signal)  # register signal
    streamer.start()
    while True:
      pass
  except KeyboardInterrupt:
    streamer.stop()


def show_gui(streamer):
  """
  Run *streamer* in GUI interface.

  """
  def _toggle_stream(button, streamer):
    """
    Toggle *button* text and *streamer* state.

    """
    if button['text'] == 'Start Stream':
      button['text'] = 'Stop Stream'
      streamer.start()
    else:
      button['text'] = 'Start Stream'
      streamer.stop()
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

  :param cmd_options: arguments for :meth:`DeskStreamer.build_commands`

  """
  streamer = DeskStreamer(**cmd_options)
  if show_commands:
    print(streamer.cmd_str_av)
    print(streamer.cmd_str_vlc)
  elif gui:
    show_gui(streamer)
  else:
    show_cli(streamer)
  return 0


def _get_args(argv=None):
  """
  Return dict with parsed arguments and options.

  """
  args = {}
  for k, v in docopt.docopt(__doc__, version=__VERSION__, argv=argv).items():
    # cleanup argument name:
    arg = (k[2:] if k.startswith('--') else k).replace('-', '_')
    # store arguments in `args`:
    if arg == 'audio_only':
      args['use_video'] = False if v else True
    elif arg == 'no_audio':
      args['use_audio'] = False if v else True
    else:
      args[arg] = v
  return args


if __name__ == '__main__':
  sys.exit(main(**_get_args()))
