Python X Keyhook
=========

Pure Python keyboard hook for recording KeyPress and KeyRelease events via Python XLib wrapper.

Features:
-----

  - written in Python 2.7 thanks to [Python-Xlib][1] wrapper
  - based on pyxhook.py library from [PyKeylogger][2]
  - keyboard events can be caught by X server before they are being propagated to desktop environment or to any application
  - events are only recorded (not grabbed) so they are still propagated to other applications
  - any key recognized by OS can be recorded (including special keys like multimedia play/pause, volume, etc.)
  - could be simply used for catching any system-wide shortcut when your app is minimized or lost focus (this feature is missing in PyQt, PyGTK, etc.)


Example usage:
----

```python
import xkeyhook

# called on KeyDown event
def key_down(event):
    ...

# called on KeyUp event
def key_up(event):
    ...

# ---------------------------------

hook = xkeyhook.HookManager()

# setup callback functions
hook.key_down_callback = key_down
hook.key_up_callback = key_up

hook.start()        # start hook thread

raw_input("\nPress Enter to quit hook...\n")
hook.cancel()       # stop hook thread
```

Requirments:
-----------

- Linux distro running on X
- Python 2.7
- python-xlib (note: xwindows must have the "record" extension present, and active.)

License
----

GNU GENERAL PUBLIC LICENSE

Version 2, June 1991


[1]:http://python-xlib.sourceforge.net/
[2]:http://sourceforge.net/projects/pykeylogger/

