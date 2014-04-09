# Stream Desktop

Capture *audio* and *video* from the desktop and stream it to the local
network using [avconv][avconv] and [vlc][vlc].


## Python Script


### Usage

```
stream_desktop.py [-n|--gui] [-a|-A] [capture options] [stream options]
stream_desktop.py --version
stream_desktop.py --help
```

### Install

You can just run the python script, no need to install any Python
dependencies.

It requires [avconv][avconv] and [vlc][vlc] thought. Install them like this:

  - Debian / Ubuntu: `sudo apt-get install libav-tools vlc`

### Setup

You can use the provided `.desktop` files to include the script in your
desktop shell. Open them in an editor and fill in the correct paths for:

- `Exec` = path to wherever you put the python script

- `Icon` = path to the PNG file you want to use for an icon

After that, copy them to `~/.local/share/applications/`.

### Settings

You can use a file to store settings in a JSON dictionary. The default
location is `~/.config/StreamDesktop/settings.json`. The supported keys
are the *capture* and *stream* long-options (with `_` instead of `-`).

``` json
{
  "port": 420,
  "res_out": "1280x720"
}
```

To create it, you can set the desired options on the commandline once and
also use `--save`.

This file gets loaded if you use the ``--load`` option.

The provided `.desktop` files use it.


## Shell Script

You can source the `stream_desktop.sh` from you `.bash_aliases` or similar to
get a quick `stream_desktop` command. The python script has more options
though.


[avconv]: http://libav.org/avconv.html
[vlc]: http://www.videolan.org/vlc/
[docopt]: http://docopt.org/
