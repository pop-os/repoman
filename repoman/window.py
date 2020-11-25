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

from .dialog import ErrorDialog
from .headerbar import Headerbar
from .stack import Stack

class Window(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_default_size(700, 400)

        self.err_dialog = None

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
        
        self.show_all()
        
        # Show an error dialog to inform the user about source errors.
        if self.stack.errors:
            self.get_repos_error_dialog()
            self.err_dialog.run()
            self.err_dialog.destroy()
    
    def get_repos_error_dialog(self):
        err_string = 'The following source files had errors and were omitted:\n'
        for file in self.stack.errors:
            err_string += f'    {file}\n'
        err_string += '\nRun '
        err_string += (
            '<span '
            'font-family="monospace" '
            'background="#333333" '
            'foreground="white" '
            '> apt-manage -b </span> '
        )
        err_string += 'for more information.'
        self.err_dialog = ErrorDialog(
            self,
            'Source File Errors',
            'dialog-warning',
            'Some sources contained errors',
            err_string
        )
        self.err_dialog.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
