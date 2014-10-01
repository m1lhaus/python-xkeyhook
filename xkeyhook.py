#!/usr/bin/python

# *******************************************************************************************
#
#   This module is based on 'pyxhook' library from PyKeylogger program.
#   Only key hook functionality has been kept from original lib.
#   The module is subject to the license terms set out below.
#
#   Modified by: Milan Herbig (m1lhaus)
#
# ******************************************************************************************
#   Copyright (C) 2008 Tim Alexander <dragonfyre13@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#       Thanks to Alex Badea <vamposdecampos@gmail.com> for writing the Record
#       demo for the xlib libraries. It helped me immensely working with these
#       in this library.
#
#       Thanks to the python-xlib team. This wouldn't have been possible without
#       your code.
#
#       REQUIREMENTS:
#       -------------
#       at least python-xlib 1.4
#       xwindows must have the "record" extension present, and active.
#
#       This file has now been somewhat extensively modified by
#       Daniel Folkinshteyn <nanotube@users.sf.net>
#       So if there are any bugs, they are probably my fault. :)
#
#       EXAMPLE USAGE:
#       -------------
#       at the bottom

import sys
import re
import threading

from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq


class HookManager(threading.Thread):
    """This is the main class. Instantiate it, and you can hand it KeyDown and KeyUp (functions in your own code)
    which execute to parse the pyxhookkeyevent class that is returned.

    This simply takes these two values for now:
    KeyDown = The function to execute when a key is pressed, if it returns anything. It hands the function an argument
    that is the pyxhookkeyevent class.
    KeyUp = The function to execute when a key is released, if it returns anything. It hands the function an argument
    that is the pyxhookkeyevent class.
    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.finished = threading.Event()

        # Give these some initial values
        self.mouse_position_x = 0
        self.mouse_position_y = 0
        self.ison = {"shift": False, "caps": False}

        # Compile our regex statements.
        self.isshift = re.compile('^Shift')
        self.iscaps = re.compile('^Caps_Lock')
        self.shiftablechar = re.compile(
            '^[a-z0-9]$|^minus$|^equal$|^bracketleft$|^bracketright$|^semicolon$|^backslash$|^apostrophe$|^comma$|^period$|^slash$|^grave$')
        self.logrelease = re.compile('.*')
        self.isspace = re.compile('^space$')

        # Assign default function actions (do nothing).
        # self.key_down_callback = lambda x: True
        self.key_down_callback = lambda x: True
        self.key_up_callback = lambda x: True

        # Hook to our display.
        self.local_dpy = display.Display()
        self.record_dpy = display.Display()

    def run(self):
        # Check if the extension is present
        if not self.record_dpy.has_extension("RECORD"):
            print >> sys.stderr, "RECORD extension not found"
            sys.exit(1)
        r = self.record_dpy.record_get_version(0, 0)
        print "RECORD extension version %d.%d" % (r.major_version, r.minor_version)

        # Create a recording context; we only want key and mouse events
        self.recording_context = self.record_dpy.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': (X.KeyPress, X.KeyRelease),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
             }])

        # Enable the context; this only returns after a call to record_disable_context,
        # while calling the callback function in the meantime
        self.record_dpy.record_enable_context(self.recording_context, self.process_events)

        # *** waits up here ***

        # Finally free the context
        self.record_dpy.record_free_context(self.recording_context)

    def cancel(self):
        self.finished.set()
        self.local_dpy.record_disable_context(self.recording_context)
        self.local_dpy.flush()

    def process_events(self, reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            print "* received swapped protocol data, cowardly ignored"
            return
        if not len(reply.data) or ord(reply.data[0]) < 2:
            # not an event
            return

        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, self.record_dpy.display, None, None)
            if event.type == X.KeyPress:
                hook_event = self.keypress_event(event)
                self.key_down_callback(hook_event)
            elif event.type == X.KeyRelease:
                hook_event = self.keyrelease_event(event)
                self.key_up_callback(hook_event)

    def keypress_event(self, event):
        matchto = self.lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))

        # This is a character that can be typed.
        if self.shiftablechar.match(self.lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))):
            if not self.ison["shift"]:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
                return self.make_key_hook_event(keysym, event)
            else:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 1)
                return self.make_key_hook_event(keysym, event)

        # Character that can NOT be typed.
        else:
            keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
            if self.isshift.match(matchto):
                self.ison["shift"] += 1
            elif self.iscaps.match(matchto):
                if not self.ison["caps"]:
                    self.ison["shift"] += 1
                    self.ison["caps"] = True
                if self.ison["caps"]:
                    self.ison["shift"] -= 1
                    self.ison["caps"] = False

            return self.make_key_hook_event(keysym, event)

    def keyrelease_event(self, event):
        if self.shiftablechar.match(self.lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))):
            if not self.ison["shift"]:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
            else:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 1)
        else:
            keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)

        matchto = self.lookup_keysym(keysym)
        if self.isshift.match(matchto):
            self.ison["shift"] -= 1

        return self.make_key_hook_event(keysym, event)

    @staticmethod
    def lookup_keysym(keysym):
        """
        need the following because XK.keysym_to_string() only does printable chars
        rather than being the correct inverse of XK.string_to_keysym()
        """
        for name in dir(XK):
            if name.startswith("XK_") and getattr(XK, name) == keysym:
                return name.lstrip("XK_")

        return "[%d]" % keysym

    def ascii_value(self, keysym):
        ascii_num = XK.string_to_keysym(self.lookup_keysym(keysym))
        if ascii_num < 256:
            return ascii_num
        else:
            return 0

    def make_key_hook_event(self, keysym, event):
        storewm = self.xwindow_info()
        if event.type == X.KeyPress:
            MessageName = "key down"
        elif event.type == X.KeyRelease:
            MessageName = "key up"
        else:
            print >> sys.stderr, 'WARNING: Unexpected event type: %s' % event.type
            return

        return XHookKeyEvent(storewm["handle"], storewm["name"], storewm["class"], self.lookup_keysym(keysym),
                             self.ascii_value(keysym), False, event.detail, MessageName)

    def xwindow_info(self):
        try:
            windowvar = self.local_dpy.get_input_focus().focus
            wmname = windowvar.get_wm_name()
            wmclass = windowvar.get_wm_class()
            wmhandle = str(windowvar)[20:30]
        except:
            ## This is to keep things running smoothly. It almost never happens, but still...
            return {"name": None, "class": None, "handle": None}

        if (wmname is None) and (wmclass is None):
            try:
                windowvar = windowvar.query_tree().parent
                wmname = windowvar.get_wm_name()
                wmclass = windowvar.get_wm_class()
                wmhandle = str(windowvar)[20:30]
            except:
                ## This is to keep things running smoothly. It almost never happens, but still...
                return {"name": None, "class": None, "handle": None}

        if wmclass is None:
            return {"name": wmname, "class": wmclass, "handle": wmhandle}
        else:
            return {"name": wmname, "class": wmclass[0], "handle": wmhandle}

    @staticmethod
    def print_event(event):
        print event


class XHookKeyEvent:
    """
    This is the class that is returned with each key event.f
    It simply creates the variables below in the class.
    
    :param Window: The handle of the window.
    :param WindowName: The name of the window.
    :param WindowProcName: The backend process for the window.
    :param Key: The key pressed, shifted to the correct caps value.
    :param Ascii: An ascii representation of the key. It returns 0 if the ascii value is not between 31 and 256.
    :param KeyID: This is just False for now. Under windows, it is the Virtual Key Code, but that's a windows-only thing.
    :param ScanCode: Please don't use this. It differs for pretty much every type of keyboard. X11 abstracts this information anyway.
    :param MessageName: "key down" or "key up".
    """

    def __init__(self, Window, WindowName, WindowProcName, Key, Ascii, KeyID, ScanCode, MessageName):
        self.Window = Window
        self.WindowName = WindowName
        self.WindowProcName = WindowProcName
        self.Key = Key
        self.Ascii = Ascii
        self.KeyID = KeyID
        self.ScanCode = ScanCode
        self.MessageName = MessageName

    def __str__(self):
        return "Window Handle: " + str(self.Window) + \
               "\nWindow Name: " + str(self.WindowName) + \
               "\nWindow's Process Name: " + str(self.WindowProcName) + \
               "\nKey Pressed: " + str(self.Key) + \
               "\nAscii Value: " + str(self.Ascii) + \
               "\nKeyID: " + str(self.KeyID) + \
               "\nScanCode: " + str(self.ScanCode) + \
               "\nMessageName: " + str(self.MessageName) + \
               "\n"


# ------------- EXAMPLE USAGE -------------------
if __name__ == "__main__":
    xhook = HookManager()

    # setup callback functions
    xhook.key_down_callback = xhook.print_event
    # xhook.key_up_callback = xhook.print_event

    xhook.start()

    raw_input("*"*49 + "\n*****" + " "*5 + "Press Enter to exit the hook!" + " "*5 + "*"*5 + "\n" + "*"*49 + "\n")
    xhook.cancel()