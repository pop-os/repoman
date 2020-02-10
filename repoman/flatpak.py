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

from os.path import splitext
from subprocess import CalledProcessError
from sys import exc_info

import gi
import logging
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')
from gi.repository import Gtk, GObject, Pango

import pyflatpak as flatpak
from pyflatpak.remotes import AddRemoteError, DeleteRemoteError

from .dialog import ErrorDialog

import gettext
gettext.bindtextdomain('repoman', '/usr/share/repoman/po')
gettext.textdomain("repoman")
_ = gettext.gettext

class AddDialog(Gtk.Dialog):

    remote_name = False

    def __init__(self, parent):

        settings = Gtk.Settings.get_default()
        header = settings.props.gtk_dialogs_use_header

        Gtk.Dialog.__init__(self, _("Add Source"), parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_ADD, Gtk.ResponseType.OK),
                             modal=1, use_header_bar=header)

        self.log = logging.getLogger("repoman.FPAddDialog")

        content_area = self.get_content_area()

        content_grid = Gtk.Grid()
        content_grid.set_margin_top(12)
        content_grid.set_margin_left(12)
        content_grid.set_margin_right(12)
        content_grid.set_margin_bottom(12)
        content_grid.set_row_spacing(6)
        content_grid.set_column_spacing(6)
        content_grid.set_halign(Gtk.Align.CENTER)
        content_grid.set_hexpand(True)
        content_area.add(content_grid)

        add_title = Gtk.Label(_("Enter Source Details"))
        Gtk.StyleContext.add_class(add_title.get_style_context(), "h2")
        content_grid.attach(add_title, 0, 0, 2, 1)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text(_("URL"))
        self.url_entry.set_activates_default(True)
        self.url_entry.connect(_("changed"), self.on_url_entry_changed)
        self.url_entry.set_width_chars(50)
        self.url_entry.set_margin_top(12)
        content_grid.attach(self.url_entry, 0, 1, 1, 1)

        self.add_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        self.add_button.set_sensitive(False)

        self.cancel_button = self.get_widget_for_response(Gtk.ResponseType.CANCEL)
        self.cancel_button.grab_focus()

        Gtk.StyleContext.add_class(self.add_button.get_style_context(),
                                   "suggested-action")
        self.add_button.grab_default()

        self.show_all()

    def on_url_entry_changed(self, entry):
        entry_text = entry.get_text()
        entry_valid = flatpak.validate(entry_text)
        try:
            self.add_button.set_sensitive(entry_valid)
        except TypeError:
            pass

    def on_insert_emoji(self, entry, data=None):
        """ We hook into this and return True. This should prevent the entry
        from showing the emoji picker.
        """
        self.log.debug('Not Showing Emoji')
        return True

class DeleteDialog(Gtk.Dialog):

    ppa_name = False

    def __init__(self, parent, remote_name):

        settings = Gtk.Settings.get_default()

        header = settings.props.gtk_dialogs_use_header

        Gtk.Dialog.__init__(self, _(f"Remove {remote_name}"), parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_REMOVE, Gtk.ResponseType.OK),
                             modal=1, use_header_bar=header)

        self.log = logging.getLogger("repoman.FPDeleteDialog")


        content_area = self.get_content_area()

        content_grid = Gtk.Grid()
        content_grid.set_margin_top(24)
        content_grid.set_margin_left(24)
        content_grid.set_margin_right(24)
        content_grid.set_margin_bottom(24)
        content_grid.set_column_spacing(12)
        content_grid.set_row_spacing(6)
        content_area.add(content_grid)

        delete_image = Gtk.Image.new_from_icon_name("dialog-warning-symbolic",
                                                Gtk.IconSize.DIALOG)
        delete_image.props.valign = Gtk.Align.START
        content_grid.attach(delete_image, 0, 0, 1, 2)

        delete_label = Gtk.Label(_("Are you sure you want to remove this source?"))
        Gtk.StyleContext.add_class(delete_label.get_style_context(), "h2")
        content_grid.attach(delete_label, 1, 0, 1, 1)

        delete_explain = Gtk.Label(_("If you remove this source, you will need to add it again to continue using it. Any software you've installed from this source will be removed."))
        delete_explain.props.wrap = True
        delete_explain.set_max_width_chars(50)
        delete_explain.set_xalign(0)
        content_grid.attach(delete_explain, 1, 1, 1, 1)

        Gtk.StyleContext.add_class(self.get_widget_for_response(Gtk.ResponseType.OK).get_style_context(),
                                   "destructive-action")

        self.show_all()

class InfoDialog(Gtk.Dialog):

    def __init__(self, parent, remote, name, option):
        self.remote_name = remote
        self.option = option
        self.remote_data = flatpak.remotes.remotes[option][remote]

        settings = Gtk.Settings.get_default()
        header = settings.props.gtk_dialogs_use_header
        super().__init__(
            _(f'{name}'),
            parent, 
            0,
            modal=1,
            use_header_bar=header
        )
        self.log = logging.getLogger('repoman.FPInfoDialog')

<<<<<<< HEAD
        self.log.debug('Data for remote %s: %s', remote, self.remote_data)
=======
        remote_info = str(flatpak.remotes.remotes[self.option][self.remote_name])
        remote_info = remote_info.replace("', '", "'\n'")
        self.log.debug(
            'Creating Info page for %s: /n %s', self.remote_name, remote_info
        )
>>>>>>> Add in disable toggle

        self.set_resizable(False)

        content_area = self.get_content_area()
        headerbar = self.get_header_bar()
        
        self.disable_switch = Gtk.Switch()
        self.disable_switch.set_active(
            flatpak.remotes.remotes[self.option][self.remote_name]
        )
        self.disable_switch.connect('state-set', self.on_switch_toggled)
        headerbar.pack_end(self.disable_switch)

        content_grid = Gtk.Grid()
        content_grid.set_halign(Gtk.Align.CENTER)
        content_grid.set_margin_top(24)
        content_grid.set_margin_bottom(24)
        content_grid.set_margin_start(24)
        content_grid.set_margin_end(24)
        content_grid.set_column_spacing(12)
        content_grid.set_row_spacing(6)
        content_area.add(content_grid)

<<<<<<< HEAD
        remote_title = self.remote_data['title']
        description = self.remote_data['about']
        url = self.remote_data['homepage']
=======
        remote_title = flatpak.remotes.remotes[self.option][self.remote_name]['title']
        description = flatpak.remotes.remotes[self.option][self.remote_name]['about']
        url = flatpak.remotes.remotes[self.option][self.remote_name]['url']
>>>>>>> Add in disable toggle

        title_label = Gtk.Label()
        title_label.set_line_wrap(True)
        title_label.set_markup(f'<b>{remote_title}</b>')
        content_grid.attach(title_label, 0, 1, 1, 1)

        name_label = Gtk.Label()
        name_label.set_markup(f'<i><small>{self.remote_name}</small></i>')
        content_grid.attach(name_label, 0, 2, 1, 1)

        description_label = Gtk.Label()
        description_label.set_margin_top(18)
        description_label.set_margin_bottom(12)
        description_label.set_line_wrap(True)
        description_label.set_max_width_chars(36)
        description_label.set_width_chars(36)
        description_label.set_text(description)
        content_grid.attach(description_label, 0, 3, 1, 1)
        
        url_button = Gtk.LinkButton.new_with_label(_('Homepage'))
        url_button.set_uri(url)
        content_grid.attach(url_button, 0, 4, 1, 1)
    
    def get_remote(self, remote_name):
        return flatpak.remotes.remotes[self.option][self.remote_name]
    
    def on_switch_toggled(self, switch, state):
        self.log.debug(
            'Setting enabled state for %s to %s', self.remote_name, state
        )
        flatpak.remotes.remote_set_enabled(self.remote_name, state)

        self.show_all()

class Flatpak(Gtk.Box):

    listiter_count = 0
    remote_name = False

    def __init__(self, parent):
        Gtk.Box.__init__(self, False, 0)
        self.parent = parent
        self.settings = Gtk.Settings()

        self.log = logging.getLogger("repoman.Flatpak")
        self.log.debug('Logging established')


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

        self.remote_liststore = Gtk.ListStore(str, str, str, str, str)
        self.view = Gtk.TreeView(self.remote_liststore)
        
        name_renderer = Gtk.CellRendererText()
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

    def on_delete_button_clicked(self, widget):
        remote = self.get_selected_remote(0)
        name = self.strip_bold_from_name(self.get_selected_remote(1))
        self.log.info('Deleting remote %s', remote)

        dialog = DeleteDialog(self.parent.parent, name)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            self.add_button.set_sensitive(False)
            self.info_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            try:
                flatpak.remotes.delete_remote(remote)
            except DeleteRemoteError:
                err = exc_info()
                self.log.exception(err)
                edialog = ErrorDialog(
                    dialog,
                    'Couldn\'t remove remote',
                    'dialog-error',
                    'Couldn\'t remove remote',
                    err[1]
                )
                edialog.run()
                edialog.destroy()
        
        dialog.destroy()
        self.generate_entries()
    
    def on_info_button_clicked(self, widget):
        remote = self.get_selected_remote(0)
        name = self.strip_bold_from_name(self.get_selected_remote(1))
        option = self.get_selected_remote(4)

        dialog = InfoDialog(self.parent.parent, remote, name, option)
        response = dialog.run()
        dialog.destroy()
    
    def strip_bold_from_name(self, name):
        name = name.replace('<b>', '')
        name = name.replace('</b>', '')
        return name
    
    def get_selected_remote(self, index):
        selection = self.view.get_selection()
        (model, pathlist) = selection.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        value = model.get_value(tree_iter, index)
        self.log.debug('Current selection: %s', value)
        return value

    def on_row_activated(self, widget, data1, data2):
        remote = self.get_selected_remote(0)
        name = self.get_selected_remote(1)
        name = name.replace('<b>', '')
        name = name.replace('</b>', '')
        self.log.info('Deleting remote %s', remote)

        dialog = DeleteDialog(self.parent.parent, name)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            flatpak.remotes.delete_remote(remote)
        
        dialog.destroy()
        self.generate_entries()

    def on_add_button_clicked(self, widget):
        dialog = AddDialog(self.parent.parent)
        response = dialog.run()
        self.log.debug('Response type: %s', response)

        if response == Gtk.ResponseType.OK:
            self.add_button.set_sensitive(False)
            self.info_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            url = dialog.url_entry.get_text().strip()
            name = splitext(url.split('/')[-1])[0]
            self.log.info('Adding flatpak source %s at %s', name, url)
            try:
                flatpak.remotes.add_remote(name, url)
            except AddRemoteError:
                err = exc_info()
                self.log.exception(err)
                edialog = ErrorDialog(
                    dialog,
                    'Couldn\'t add remote',
                    'dialog-error',
                    'Couldn\'t add remote',
                    err[1]
                )
                edialog.run()
                edialog.destroy()
            
            dialog.destroy()
        else:
            dialog.destroy()
        
        self.generate_entries()

    def generate_entries(self):
        self.remote_liststore.clear()

        # remote_liststore = []
        remotes = {}
        for option in flatpak.remotes.remotes:
            for remote in flatpak.remotes.remotes[option]:
                remotes[remote] = flatpak.remotes.remotes[option][remote]
        
        for remote in remotes:
            # remote_liststore.append(
            self.remote_liststore.append(
                [
                    remotes[remote]["name"],
                    f'<b>{remotes[remote]["title"]}</b>',
                    remotes[remote]["about"],
                    remotes[remote]["url"],
                    remotes[remote]["option"]
                ]
            )
        self.add_button.set_sensitive(True)

    def on_row_selected(self, widget):
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

    def throw_error_dialog(self, message, msg_type):
        if msg_type == "error":
            msg_type = Gtk.MessageType.ERROR
        dialog = Gtk.MessageDialog(self.parent.parent, 0, msg_type,
                                   Gtk.ButtonsType.CLOSE, message)
        dialog.run()
        dialog.destroy()
