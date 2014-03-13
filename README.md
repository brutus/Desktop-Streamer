# Stream Desktop

Capture *audio* and *video* from the desktop and stream it to the local
network using [avconv][avconv] and [vlc][vlc].


## Usage

```
stream_desktop.py [-n|--gui] [-a|-A] [options]
stream_desktop.py --version
stream_desktop.py --help
```


## Python Script

### Install

You can just run the python script, no need to install.

It requires [docopt][docopt] thought. Install it like this:

  `pip install --user docopt`

### Setup

You can use the provided `.desktop` files to include the script in your
desktop shell. Open them in an editor and fill in the correct paths:

* `Exec` = path to wherever you put the python script

* `Icon` = path to the PNG file you want to use for an icon

After that copy them to `~/.local/share/applications/`.


## Shell Script

You can source the `stream_desktop.sh` from you `.bash_aliases` or similar to
get a quick `stream_desktop` command. The python script has more options
though.


[avconv]: http://libav.org/avconv.html
[vlc]: http://www.videolan.org/vlc/
[docopt]: http://docopt.org/
