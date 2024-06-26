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

from gettext import gettext as _
import logging

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

from . import repo
from .dialog import AddDialog, DeleteDialog, EditDialog, ErrorDialog

class List(Gtk.Box):

    listiter_count = 0

    def __init__(self, parent):
        Gtk.Box.__init__(self, False, 0)
        self.parent = parent

        self.settings = Gtk.Settings()

        self.log = logging.getLogger("repoman.List")
        self.log.debug('Logging established')


        self.content_grid = Gtk.Grid()
        self.content_grid.set_margin_left(12)
        self.content_grid.set_margin_top(24)
        self.content_grid.set_margin_right(12)
        self.content_grid.set_margin_bottom(12)
        self.content_grid.set_hexpand(True)
        self.content_grid.set_vexpand(True)
        self.add(self.content_grid)

        sources_title = Gtk.Label(_("Extra Sources"))
        sources_title.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(sources_title.get_style_context(), "h2")
        self.content_grid.attach(sources_title, 0, 0, 1, 1)

        sources_label = Gtk.Label(_("These sources are for software provided by a third party. They may present a security risk or cause system instability. Only add sources that you trust."))
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

        self.ppa_liststore = Gtk.ListStore(str, str, str)
        self.view = Gtk.TreeView(self.ppa_liststore)
        renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn(_("Source"), renderer, markup=0)
        self.view.append_column(name_column)
        uri_column = Gtk.TreeViewColumn(_('URI'), renderer, markup=1)
        self.view.append_column(uri_column)
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

        # edit button
        self.edit_button = Gtk.ToolButton()
        self.edit_button.set_sensitive(False)
        self.edit_button.set_icon_name("edit-symbolic")
        Gtk.StyleContext.add_class(self.edit_button.get_style_context(),
                                   "image-button")
        self.edit_button.set_tooltip_text(_("Modify Selected Source"))
        self.edit_button.connect("clicked", self.on_edit_button_clicked)

        # delete button
        self.delete_button = Gtk.ToolButton()
        self.delete_button.set_sensitive(False)
        self.delete_button.set_icon_name("edit-delete-symbolic")
        Gtk.StyleContext.add_class(self.delete_button.get_style_context(),
                                   "image-button")
        self.delete_button.set_tooltip_text(_("Delete Selected Source"))
        self.delete_button.connect("clicked", self.on_delete_button_clicked)

        action_bar = Gtk.Toolbar()
        action_bar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        Gtk.StyleContext.add_class(action_bar.get_style_context(),
                                   "inline-toolbar")
        action_bar.insert(self.delete_button, 0)
        action_bar.insert(self.edit_button, 0)
        action_bar.insert(self.add_button, 0)
        list_grid.attach(action_bar, 0, 1, 1, 1)

        # Watch the config directory for changes, so we can reload if so
        self.file = Gio.File.new_for_path('/etc/apt/sources.list.d/')
        self.monitor = self.file.monitor_directory(Gio.FileMonitorFlags.NONE)
        self.monitor.connect('changed', self.on_config_changed)
        self.log.debug('Monitor Created: %s', self.monitor)

        self.generate_entries()
    
    def on_delete_button_clicked(self, widget):
        selec = self.view.get_selection()
        (model, pathlist) = selec.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        repo_name = model.get_value(tree_iter, 2)
        self.log.debug('Deleting Source: %s', repo_name)
        self.do_delete(repo_name)
    
    def do_delete(self, repo_name):
        file = repo.sources[repo_name].file
        source = file.get_source_by_ident(repo_name)
        dialog = DeleteDialog(self.parent.parent, source.name)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.add_button.set_sensitive(False)
            self.edit_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            dialog.destroy()
            try:
                file.remove_source(repo_name)
                file.save()
                repo.load_all_sources()
                self.generate_entries()
                success = True
            except:
                success = False
            
        else:
            dialog.destroy()
            # We didn't remove the source... but that was intentional. 
            # Don't display an error if the user clicks "Cancel"
            success = True
        
        if not success:
            error_dialog = Gtk.MessageDialog(
                transient_for=self.parent.parent,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CANCEL,
                text="Could not remove source",
            )
            error_dialog.format_secondary_text(
                f"The source {repo_name} could not be removed."
            )
            error_dialog.run()
            error_dialog.destroy()

    def on_edit_button_clicked(self, widget):
        selec = self.view.get_selection()
        (model, pathlist) = selec.get_selected_rows()
        tree_iter = model.get_iter(pathlist[0])
        ident = model.get_value(tree_iter, 2)
        self.log.info("Source to edit: %s" % ident)
        if ident == 'x-repoman-legacy-sources':
            repo.edit_system_legacy_sources_list()
        else:
            source = repo.sources[ident]
            self.do_edit(source)
    
    def edit_sources_list(self):
        repo.edit_system_legacy_sources_list()

    def on_row_activated(self, widget, data1, data2):
        tree_iter = self.ppa_liststore.get_iter(data1)
        value = self.ppa_liststore.get_value(tree_iter, 1)
        self.log.info("PPA to edit: %s" % value)
        self.do_edit(value)
    
    def sync_source(self, source, dialog):
        """Sync data from a dialog into a source"""
        source.name = dialog.name_entry.get_text()
        source.sourcecode_enabled = dialog.source_switch.get_state()
        source.uris = dialog.uri_entry.get_text().split()
        source.suites = dialog.version_entry.get_text().split()
        source.components = dialog.component_entry.get_text().split()
        source.enabled = dialog.enabled_switch.get_state()

    def do_edit(self, source, key:bool = False):
        """ Perform an edit action. """
        self.log.debug('Editing %s', source)
        dialog = EditDialog(self.parent.parent, source)
        if key:
            dialog.content_stack.set_visible_child_name('key')
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            try:
                file = source.file
                out_source = file.get_source_by_ident(source.ident)
                self.sync_source(out_source, dialog)
                self.log.debug('Saving new source %s', source)
                out_source.save()
                self.log.debug('Source saved')
            except Exception as err:
                self.log.error(
                    'Could not edit mirror %s: %s', source.ident, str(err)
                )
                err_dialog = repo.get_error_messagedialog(
                    self.parent.parent,
                    f'Could not save source',
                    err,
                    f'{source.name} could not be saved'
                )
                err_dialog.run()
                err_dialog.destroy()
        elif response == Gtk.ResponseType.APPLY:
            try:
                file = source.file
                out_source = file.get_source_by_ident(source.ident)
                self.sync_source(out_source, dialog)
                if dialog.keytype == 'path':
                    out_source.signed_by = dialog.key_data
                else:
                    out_source.key = dialog.key
                    out_source.signed_by = str(out_source.key.path)
                self.log.debug('Saving new source %s', source)
                out_source.save()
                self.log.debug('Source saved')
            except Exception as err:
                self.log.error(
                    'Could not edit mirror %s: %s', source.ident, str(err)
                )
                err_dialog = repo.get_error_messagedialog(
                    self.parent.parent,
                    f'Could not save source',
                    err,
                    f'{source.name} could not be saved'
                )
                err_dialog.run()
                err_dialog.destroy()
        elif response == Gtk.ResponseType.REJECT:
            try:
                file = source.file
                out_source = file.get_source_by_ident(source.ident)
                self.sync_source(out_source, dialog)
                old_key = out_source.key
                out_source.key = None
                out_source.signed_by = ''
                multi_key: bool = False
                for other_source in repo.sources.values():
                    if other_source.ident == out_source.ident:
                        continue
                    if other_source.key == old_key:
                        self.log.debug(
                            'Found key in use with %s', other_source.ident
                        )
                        multi_key = True
                        break
                if multi_key:
                    self.log.info(
                        'Key file %s in use with another key, not deleting',
                        old_key.path
                    )
                else:
                    self.log.warning(
                        'No other source found using the key %s, deleting',
                        old_key.path
                    )
                    old_key.delete_key()
                self.log.debug('Saving new source %s', source)
                out_source.save()
                self.log.debug('Source saved')
            except Exception as err:
                self.log.error(
                    'Could not edit mirror %s: %s', source.ident, str(err)
                )
                err_dialog = repo.get_error_messagedialog(
                    self.parent.parent,
                    f'Could not save source',
                    err,
                    f'{source.name} could not be saved'
                )
                err_dialog.run()
                err_dialog.destroy()
        else:
            self.log.debug('Cancelling edit')

        self.log.debug('New source: %s', dialog.source)
        dialog.destroy()

    def on_add_button_clicked(self, widget):
        dialog = AddDialog(self.parent.parent)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.add_button.set_sensitive(False)
            self.edit_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)
            url = dialog.repo_entry.get_text().strip()
            repo.add_source(url, dialog)
        else:
            dialog.destroy()
        
        # Ensure this is set sensitive again
        self.add_button.set_sensitive(True)

    def generate_entries(self, *args, **kwargs):
        self.log.debug('Generating list of repos')
        repo.load_all_sources()
        self.ppa_liststore.clear()

        for i in repo.sources:
            self.log.debug('Source: %s', i)

        
        # Print a warning to console about source file errors.
        if repo.errors:
            err_string = 'The following source files have errors:\n\n'
            for file in repo.errors:
                err_string += f'{file}\n'
            self.log.warning(err_string)

        # self.log.debug('Sources found:\n%s', repo.sources)
        for i in repo.sources:
            if i == 'system':
                continue
            source = repo.sources[i]
            try:
                if source.enabled.get_bool():
                    self.log.debug('Source: %s, URIs: %s', source.name, source.uris[0])
                    self.ppa_liststore.insert_with_valuesv(
                        -1,
                        [0, 1, 2],
                        [f'<b>{source.name}</b>', source.uris[0], source.ident]
                    )
            except AttributeError:
                # Skip any weirdly malformed sources
                pass

        for i in repo.sources:
            source = repo.sources[i]
            try:
                if not source.enabled.get_bool(): 
                    self.ppa_liststore.insert_with_valuesv(
                        -1,
                        [0, 1, 2],
                        [source.name, source.uris[0], source.ident]
                    )
            except AttributeError:
                pass
            
        self.add_button.set_sensitive(True)

    def on_config_changed(self, monitor, file, other_file, event_type):
        self.log.debug('Installation changed, regenerating list')
        self.generate_entries()

    def on_row_selected(self, widget):
        (model, pathlist) = widget.get_selected_rows()
        if pathlist:
            self.edit_button.set_sensitive(True)
            for path in pathlist :
                tree_iter = model.get_iter(path)
                repo_name = model.get_value(tree_iter,2)
                self.remote_name = repo_name
                if repo_name != 'x-repoman-legacy-sources':
                    self.delete_button.set_sensitive(True)
                else:
                    self.delete_button.set_sensitive(False)
        else:
            self.edit_button.set_sensitive(False)
            self.delete_button.set_sensitive(False)

    def throw_error_dialog(self, message, msg_type):
        dialog = ErrorDialog(
                    self.parent,
                    'Couldn\'t add source',
                    'dialog-error',
                    'Couldn\'t add source',
                    message
                )
        dialog.run()
        dialog.destroy()
