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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from .headerbar import Headerbar
from .stack import Stack

class Window(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)

        self.hbar = Headerbar(self)
        self.set_titlebar(self.hbar)

        self.stack = Stack(self)
        self.add(self.stack)

        self.hbar.switcher.set_stack(self.stack.stack)

        self.screen = Gdk.Screen.get_default()
        self.css_provider = Gtk.CssProvider()
        try:
            self.css_provider.load_from_path('data/style.css')
        except GLib.Error:
            self.css_provider.load_from_path('/usr/share/repoman/style.css')
        self.context = Gtk.StyleContext()
        self.context.add_provider_for_screen(self.screen, self.css_provider,
          Gtk.STYLE_PROVIDER_PRIORITY_USER)

