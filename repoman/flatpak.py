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
from os.path import splitext
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, GObject, GLib, Gio, Pango

from .dialog import ErrorDialog, AddDialog, DeleteDialog, InfoDialog
from . import flatpak_helper as helper

import gettext
gettext.bindtextdomain('repoman', '/usr/share/repoman/po')
gettext.textdomain("repoman")
_ = gettext.gettext

class Flatpak(Gtk.Box):

    listiter_count = 0
    remote_name = False

    def __init__(self, parent):
        Gtk.Box.__init__(self, False, 0)
        self.parent = parent
        self.settings = Gtk.Settings()

        self.log = logging.getLogger("repoman.Flatpak")
        self.log.debug('Logging established')

        syst_install = helper.get_installation_for_type('system')
        user_install = helper.get_installation_for_type('user')

        self.log.debug('Setting up installation monitors')
        self.syst_monitor = syst_install.create_monitor()
        self.syst_monitor.connect('changed', self.on_installation_changed)
        self.user_monitor = user_install.create_monitor()
        self.user_monitor.connect('changed', self.on_installation_changed)

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
        Gtk.StyleContext.add_class(
            list_window.get_style_context(), "list_window"
        )
        list_grid.attach(list_window, 0, 0, 1, 1)

        self.remote_liststore = Gtk.ListStore(str, str, str, str, str)
        self.view = Gtk.TreeView(self.remote_liststore)
        
        name_renderer = Gtk.CellRendererText()
        name_renderer.props.weight = 700
        name_renderer.props.wrap_mode = Pango.WrapMode.WORD_CHAR
        name_renderer.props.wrap_width = 120
        name_column = Gtk.TreeViewColumn(_('Source'), name_renderer, markup=1)
        self.view.append_column(name_column)

        url_renderer = Gtk.CellRendererText()
        url_column = Gtk.TreeViewColumn(_('URL'), url_renderer, markup=3)
        url_column.set_expand(True)
        self.view.append_column(url_column)

        option_renderer = Gtk.CellRendererText()
        option_column = Gtk.TreeViewColumn(_('Type'), option_renderer, markup=4)
        option_column.set_min_width(80)
        self.view.append_column(option_column)

        self.view.set_hexpand(True)
        self.view.set_vexpand(True)
        self.tree_selection = self.view.get_selection()
        self.tree_selection.connect('changed', self.on_row_selected)
        list_window.add(self.view)

        # add button
        self.add_button = Gtk.ToolButton()
        self.add_button.set_sensitive(False)
        self.add_button.set_icon_name("list-add-symbolic")
        Gtk.StyleContext.add_class(self.add_button.get_style_context(),
                                   "image-button")
        self.add_button.set_tooltip_text(_("Add New Source"))
        self.add_button.connect("clicked", self.on_add_button_clicked)

        # info button
        self.info_button = Gtk.ToolButton()
        self.info_button.set_sensitive(False)
        self.info_button.set_icon_name('help-info-symbolic')
        Gtk.StyleContext.add_class(self.add_button.get_style_context(),
                                   "image-button")
        self.info_button.set_tooltip_text(_('Remote Info'))
        self.info_button.connect('clicked', self.on_info_button_clicked)

        # delete button
        self.delete_button = Gtk.ToolButton()
        self.delete_button.set_sensitive(False)
        self.delete_button.set_icon_name("edit-delete-symbolic")
        Gtk.StyleContext.add_class(self.delete_button.get_style_context(),
                                   "image-button")
        self.delete_button.set_tooltip_text(_("Remove Selected Source"))
        self.delete_button.connect("clicked", self.on_delete_button_clicked)

        action_bar = Gtk.Toolbar()
        action_bar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        Gtk.StyleContext.add_class(action_bar.get_style_context(),
                                   "inline-toolbar")
        action_bar.insert(self.delete_button, 0)
        action_bar.insert(self.info_button, 0)
        action_bar.insert(self.add_button, 0)
        list_grid.attach(action_bar, 0, 1, 1, 1)

        self.generate_entries()

    def set_items_insensitive(self):
        """ Sets all of the buttons in the list to be insensitive/disabled."""
        self.add_button.set_sensitive(False)
        self.info_button.set_sensitive(False)
        self.delete_button.set_sensitive(False)
        self.view.set_sensitive(False)

    def on_delete_button_clicked(self, widget):
        """ Delete selected remote."""
        name, title, comment, url, option = self.get_selected_remote()
        installation = helper.get_installation_for_type(option)
        self.log.info('Deleting remote %s', name)
        removed_refs = helper.get_installed_refs_from_remote(name, option)
        self.log.warning('Removing %s will remove the following refs:')
        for ref in removed_refs:
            self.log.warning(
                '    %s (%s)', ref.get_name(), ref.get_appdata_name()
            )

        dialog = DeleteDialog(
            self.parent.parent, title, flatpak=True, refs=removed_refs
        )
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
            self.parent.parent.hbar.spinner.start()
            self.set_items_insensitive()
            
            helper.delete_remote(self, name, option)
        else:
            dialog.destroy()
    
    def on_info_button_clicked(self, widget):
        """ Display info dialog for the selected remote."""
        name, title, comment, url, option = self.get_selected_remote()

        dialog = InfoDialog(self.parent.parent, name, option)
        dialog.run()
        dialog.destroy()
        self.generate_entries()
    
    def get_selected_remote(self):
        """ Get's the currently selected row's data.
        
        Returns:
            (name, title, comment, url, option)
        """
        selection = self.view.get_selection()
        (model, pathlist) = selection.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        # This tuple is (name, title, comment, url, option)
        value = tuple(
            model.get_value(tree_iter, index) for index in range(0, 5)
        )
        self.log.debug('Current selection: %s', value)
        return value

    def on_add_button_clicked(self, widget):
        """Show add dialog when button clicked."""
        dialog = AddDialog(self.parent.parent, flatpak=True)
        response = dialog.run()
        self.log.debug('Response type: %s', response)

        if response == Gtk.ResponseType.OK:
            url = dialog.repo_entry.get_text().strip()
            name = splitext(url.split('/')[-1])[0]
            dialog.destroy()
            self.set_items_insensitive()
            self.log.info('Adding flatpakrepo %s at %s', name, url)
            helper.add_remote(self, name, url, 'User')
        else:
            dialog.destroy()

    def generate_entries(self):
        """ Clear the list of entries and regenerate it."""
        self.remote_liststore.clear()

        for option in ['User', 'System']:
            self.log.debug('Getting %s remotes', option)
            for remote in helper.get_remotes(option):
                self.log.debug('Found remote: %s', remote.get_name())
                if remote.get_title():
                    title = remote.get_title()
                else:
                    title = remote.get_name()

                self.remote_liststore.append([
                    remote.get_name(),
                    title,
                    remote.get_comment(),
                    remote.get_url(),
                    option
                ])
        
        self.add_button.set_sensitive(True)
        self.show_all()
    
    def on_installation_changed(self, monitor, file, other_file, event_type):
        self.log.debug('Installation changed, regenerating list')
        self.generate_entries()

    def on_row_selected(self, widget):
        """Handler when a row is selected."""
        (model, pathlist) = widget.get_selected_rows()
        if pathlist:
            self.info_button.set_sensitive(True)
            self.delete_button.set_sensitive(True)
            for path in pathlist :
                tree_iter = model.get_iter(path)
                value = model.get_value(tree_iter,1)
                self.remote_name = value
        else:
            self.info_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)

    def throw_error_dialog(self, message, msg_type='error'):
        """ Display an error message ina graphical dialog.

        Arguments:
            message (str): The message to display.
            msg_type (str): The style of the message to display.
        """
        dialog = ErrorDialog(
            self.parent, 'Couldn\'t add source', 'dialog-error',
            'Couldn\'t add source', message
        )
        dialog.run()
        dialog.destroy()
