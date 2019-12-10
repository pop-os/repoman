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
import logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import pyflatpak

from .dialog import AddDialog, EditDialog
import gettext
gettext.bindtextdomain('repoman', '/usr/share/repoman/po')
gettext.textdomain("repoman")
_ = gettext.gettext

class Flatpak(Gtk.Box):

    listiter_count = 0
    ppa_name = False

    def __init__(self, parent):
        Gtk.Box.__init__(self, False, 0)
        self.parent = parent

        self.settings = Gtk.Settings()

        self.log = logging.getLogger("repoman.Flatpak")
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        self.log.addHandler(handler)
        self.log.setLevel(logging.WARNING)

        self.content_grid = Gtk.Grid()
        self.content_grid.set_margin_left(12)
        self.content_grid.set_margin_top(24)
        self.content_grid.set_margin_right(12)
        self.content_grid.set_margin_bottom(12)
        self.content_grid.set_hexpand(True)
        self.content_grid.set_vexpand(True)
        self.add(self.content_grid)

        sources_title = Gtk.Label(_("Flatpak Sources"))
        sources_title.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(sources_title.get_style_context(), "h2")
        self.content_grid.attach(sources_title, 0, 0, 1, 1)

        sources_label = Gtk.Label(_("These sources are for software provided via Flatpak. They may present a security risk. Only add sources that you trust."))
        sources_label.set_line_wrap(True)
        sources_label.set_justify(Gtk.Justification.FILL)
        sources_label.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(sources_label.get_style_context(), "description")
        self.content_grid.attach(sources_label, 0, 1, 1, 1)

        list_grid = Gtk.Grid()
        self.content_grid.attach(list_grid, 0, 2, 1, 1)
        list_window = Gtk.ScrolledWindow()
        Gtk.StyleContext.add_class(list_window.get_style_context(), "list_window")
        list_grid.attach(list_window, 0, 0, 1, 1)

        self.ppa_liststore = Gtk.ListStore(str, str)
        self.view = Gtk.TreeView(self.ppa_liststore)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(_("Source"), renderer, markup=0)
        self.view.append_column(column)
        self.view.set_hexpand(True)
        self.view.set_vexpand(True)
        self.view.connect("row-activated", self.on_row_activated)
        tree_selection = self.view.get_selection()
        tree_selection.connect('changed', self.on_row_change)
        list_window.add(self.view)

        # add button
        add_button = Gtk.ToolButton()
        add_button.set_icon_name("list-add-symbolic")
        Gtk.StyleContext.add_class(add_button.get_style_context(),
                                   "image-button")
        add_button.set_tooltip_text(_("Add New Source"))
        add_button.connect("clicked", self.on_add_button_clicked)

        # edit button
        delete_button = Gtk.ToolButton()
        delete_button.set_icon_name("edit-delete-symbolic")
        Gtk.StyleContext.add_class(delete_button.get_style_context(),
                                   "image-button")
        delete_button.set_tooltip_text(_("Remove Selected Source"))
        delete_button.connect("clicked", self.on_delete_button_clicked)

        action_bar = Gtk.Toolbar()
        action_bar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        Gtk.StyleContext.add_class(action_bar.get_style_context(),
                                   "inline-toolbar")
        action_bar.insert(delete_button, 0)
        action_bar.insert(add_button, 0)
        list_grid.attach(action_bar, 0, 1, 1, 1)

        self.generate_entries()

    def on_delete_button_clicked(self, widget):
        pass

    def on_row_activated(self, widget, data1, data2):
        tree_iter = self.ppa_liststore.get_iter(data1)
        value = self.ppa_liststore.get_value(tree_iter, 1)
        self.log.info("PPA to edit: %s" % value)

    def do_edit(self, repo):
        pass
        

    def on_add_button_clicked(self, widget):
        pass

    def generate_entries(self):
        pass

    def on_row_change(self, widget):
        (model, pathlist) = widget.get_selected_rows()
        for path in pathlist :
            print(pathlist) #DEBUG

    def throw_error_dialog(self, message, msg_type):
        if msg_type == "error":
            msg_type = Gtk.MessageType.ERROR
        dialog = Gtk.MessageDialog(self.parent.parent, 0, msg_type,
                                   Gtk.ButtonsType.CLOSE, message)
        dialog.run()
        dialog.destroy()
