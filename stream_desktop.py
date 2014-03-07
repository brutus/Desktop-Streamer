#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Capture *audio* and *video* from desktop and stream it to the local network.

Usage:
  stream_desktop.py [-n] [-a|-A] [options]

Options:
 -n, --show-commands  don't do anything, just show the commands
 -a, --audio-only  only export audio
 -A, --no-audio  don't export audio
 -f <INT>, --framerate=<INT>  the framerate to use for the stream [default: 25]
 -r <WIDTHxHIGHT>, --res-in=<WIDTHxHIGHT>  the size of the capture area [default: 1920x1080]
 -R <WIDTHxHIGHT>, --res-out=<WIDTHxHIGHT>  transcode to this output resolution [default: 1280x720]
 -p <INT>, --port=<INT>  serv the stream on this port on all devices [default: 1312]

"""

import sys
import shlex

import docopt

from subprocess import PIPE, Popen


__VERSION__ = '0.1'


def build_commands(
  use_audio, use_video,
  framerate, res_in, res_out,
  port
):
  """
  Return tuple of formated `avconv` and `vlc` commands, each as a list.

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
  av_cmd = (
    "avconv {audio} {video} -threads 0 -f mpegts -"
  ).format(
    audio=(av_audio if use_audio else ''),
    video=(av_video if use_video else ''),
  )
  vlc_cmd = (
    "cvlc "
    " -I dummy - "
    "--sout=#std{{access=http,mux=ts,dst=:{port}}}"
  ).format(
    port=port
  )
  # build command list
  return (
    shlex.split(av_cmd, posix=False),
    shlex.split(vlc_cmd, posix=False)
  )


def run_commands(av_cmd, vlc_cmd):
  """
  Run *av_cmd* piped to *vlc_cmd*.

  """
  avconv = Popen(av_cmd, stdout=PIPE)
  vlc = Popen(vlc_cmd, stdin=avconv.stdout, stdout=PIPE)
  avconv.stdout.close()
  return vlc.communicate()[0]


def main(show_commands=False, **cmd_options):
  """
  Format commands according to *args* and run them.

  If *show_commands* is set, only print the commands.

  :param cmd_options: arguments for :func:`build_commands`

  """
  av_cmd, vlc_cmd = build_commands(**cmd_options)
  if show_commands:
    print(' '.join(av_cmd))
    print(' '.join(vlc_cmd))
    ret = 0
  else:
    ret = run_commands(av_cmd, vlc_cmd)
  return ret


def get_args(argv=None):
  """
  Return dict with parsed arguments and options.

  """
  args = {
    'use_audio': True,
    'use_video': True
  }
  for k, v in docopt.docopt(__doc__, version=__VERSION__, argv=argv).items():
    arg = k[2:] if k.startswith('--') else k
    arg = arg.replace('-', '_')
    if arg == 'audio_only':
      if v:
        args['use_video'] = False
    elif arg == 'no_audio':
      if v:
        args['use_audio'] = False
    else:
      args[arg] = v
  return args


if __name__ == '__main__':
  sys.exit(main(**get_args()))
