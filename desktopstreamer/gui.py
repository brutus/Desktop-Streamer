# -*- coding: UTF-8 -*-

"""
A GUI interface for :class:`desktopstreamer.DesktopStreamer`.

"""

from __future__ import absolute_import

import tkMessageBox
import Tkinter as tk

from . import DesktopStreamerError


__all__ = ['DSGui', 'show_gui']


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


def show_gui(streamer):
  """
  Run *streamer* from GUI interface.

  """
  root = tk.Tk()
  gui = DSGui(root, streamer)
  root.mainloop()  # show GUI and wait for it to end
  return gui.return_code
