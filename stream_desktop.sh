#!/bin/bash

stream_desktop() {
  local FRAMERATE=25
  local RES_IN='1920x1080'
  local RES_OUT='1280x720'
  local PORT=1312
  local av_opts="-f alsa -ac 2 -i pulse -f x11grab -r $FRAMERATE -s $RES_IN -i :0.0 -acodec libmp3lame -vcodec libx264 -preset ultrafast -s $RES_OUT -threads 0 -f mpegts"
  local vlc_opts="--sout=#std{access=http,mux=ts,dst=:$PORT}"
  avconv $av_opts - | cvlc -I dummy - $vlc_opts
}
