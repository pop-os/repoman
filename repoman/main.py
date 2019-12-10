#!/usr/bin/python3
'''
   Copyright 2017 Mirko Brombin (brombinmirko@gmail.com)
   Copyright 2017 Ian Santopietro (ian@system76.com)

   This file is part of Repoman.

    Repoman is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Repoman is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Repoman.  If not, see <http://www.gnu.org/licenses/>.
'''

import dbus
import logging
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

try:
    from systemd.journal import JournalHandler
except ImportError:
    JournalHandler = False

from .window import Window

bus = dbus.SystemBus()
privileged_object = bus.get_object('org.pop_os.repoman', '/PPA')

class Application(Gtk.Application):

    def do_activate(self):

        self.win = Window()
        self.win.set_default_size(700, 400)
        self.win.connect("delete-event", self.application_quit)
        self.win.show_all()
        self.win.stack.updates.noti_grid.hide()
        self.win.stack.updates.notifications_title.hide()
        self.win.stack.updates.notifications_label.hide()

        Gtk.main()
    
    def application_quit(self, widget, data=None):
        privileged_object.exit()
        Gtk.main_quit()

app = Application()

style_provider = Gtk.CssProvider()
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(), style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

app.run()
