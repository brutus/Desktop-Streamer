from setuptools import setup

from desktopstreamer import __version__ as version


with open('README.rst') as fh:
  long_description = fh.read()


setup(
  name='DesktopStreamer',
  version=version,
  description='Capture A/V from the desktop and stream it to the local network.',
  long_description=long_description,
  author='Brutus [dmc]',
  author_email='brutus.dmc@googlemail.com',
  url='https://github.com/brutus/Desktop-Streamer/',
  license='GPLv3',
  packages=['desktopstreamer'],
  data_files=[
    # ('share/icons/hicolor/scalable/apps', ['data/desktopstreamer.svg']),
    ('share/icons/hicolor/64x64/apps', ['data/desktopstreamer.png']),
    ('share/applications', ['data/StreamDesktop.desktop'])
  ],
  entry_points={
    'console_scripts': [
      'stream_desktop=desktopstreamer:main',
    ],
  },
)
