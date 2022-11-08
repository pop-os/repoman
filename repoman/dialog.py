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

import logging
from datetime import date

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # type: ignore
 
from gettext import gettext as _ 

try:
    from . import flatpak_helper 
except (ImportError, ValueError):
    pass
from . import repo

settings = Gtk.Settings.get_default()
header = settings.props.gtk_dialogs_use_header
header = True

class ErrorDialog(Gtk.Dialog):

    def __init__(self, parent, dialog_title, dialog_icon,
                 message_title, message_text):
                 
        super().__init__(use_header_bar=header, modal=1)
        self.set_deletable(False)
        self.set_transient_for(parent)

        self.log = logging.getLogger("repoman.ErrorDialog")
        
        self.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.OK)

        content_area = self.get_content_area()

        content_grid = Gtk.Grid()
        content_grid.set_margin_top(24)
        content_grid.set_margin_left(24)
        content_grid.set_margin_right(24)
        content_grid.set_margin_bottom(24)
        content_grid.set_column_spacing(36)
        content_grid.set_row_spacing(12)
        content_area.add(content_grid)

        error_image = Gtk.Image.new_from_icon_name(dialog_icon,
                                                   Gtk.IconSize.DIALOG)
        content_grid.attach(error_image, 0, 0, 1, 2)

        dialog_label = Gtk.Label()
        dialog_label.set_markup(f'<b>{message_title}</b>')
        dialog_message = Gtk.Label()
        dialog_message.set_markup(message_text)
        content_grid.attach(dialog_label, 1, 0, 1, 1)
        content_grid.attach(dialog_message, 1, 1, 1, 1)

        self.show_all()

class AddDialog(Gtk.Dialog):

    ppa_name = False

    def __init__(self, parent, flatpak=False):
        Gtk.Dialog.__init__(self, _("Add Source"), parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_ADD, Gtk.ResponseType.OK),
                             modal=1, use_header_bar=header)

        self.log = logging.getLogger("repoman.AddDialog")
        self.flatpak = flatpak

        content_area = self.get_content_area()

        content_grid = Gtk.Grid()
        content_grid.set_margin_top(24)
        content_grid.set_margin_left(12)
        content_grid.set_margin_right(12)
        content_grid.set_margin_bottom(12)
        content_grid.set_row_spacing(6)
        content_grid.set_halign(Gtk.Align.CENTER)
        content_grid.set_hexpand(True)
        content_area.add(content_grid)

        self.title_spinner = Gtk.Stack()
        self.title_spinner.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.title_spinner.set_transition_duration(200)
        self.title_spinner.set_homogeneous(True)
        self.title_spinner.set_halign(Gtk.Align.CENTER)
        content_grid.attach(self.title_spinner, 0, 0, 1, 1)

        add_grid = Gtk.Grid()

        add_title = Gtk.Label(_("Enter Source Details"))
        Gtk.StyleContext.add_class(add_title.get_style_context(), "h2")
        add_grid.attach(add_title, 0, 0, 1, 1)

        add_label = Gtk.Label(_("e.g. ppa:mirkobrombin/ppa"))
        if not self.flatpak:
            add_grid.attach(add_label, 0, 1, 1, 1)
        
        self.title_spinner.add_named(add_grid, 'title')

        self.spinner = Gtk.Spinner()
        self.spinner.stop()
        self.title_spinner.add_named(self.spinner, 'spinner')

        self.repo_entry = Gtk.Entry()
        self.repo_entry.set_placeholder_text(_("Source Line"))
        self.repo_entry.set_activates_default(True)
        self.repo_entry.connect("changed", self.on_entry_changed)
        self.repo_entry.set_width_chars(50)
        self.repo_entry.set_margin_top(12)
        content_grid.attach(self.repo_entry, 0, 2, 1, 1)

        self.add_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        self.add_button.set_sensitive(False)

        Gtk.StyleContext.add_class(self.add_button.get_style_context(),
                                   "suggested-action")
        self.add_button.grab_default()

        self.show_all()

    def on_entry_changed(self, widget):
        entry_text = widget.get_text().strip()
        entry_valid = False
        self.log.debug('Using Flatpak validator: %s', self.flatpak)

        # Validate differently based on APT vs Flatpak
        if self.flatpak:
            entry_valid = flatpak_helper.validate_flatpakrepo(entry_text)
        
        else:
            entry_valid = repo.validate(entry_text)
        
        entry_isshortcut = entry_text in ['ppa', 'popdev']
        entry_isdeb = entry_text.startswith('deb')

        # If we're dealing with a plain URL, it can't have spaces
        if not entry_isshortcut and not entry_isdeb:
            uri = entry_text.split()
            if len(uri) != 1:
                entry_valid = False
        
        # deb lines must have at least three elements (type, URI, suite)
        if entry_isdeb:
            line = entry_text.split()
            if len(line) < 3:
                entry_valid = False

        # Set the add button's sensitivity based on the results of validation.
        try:
            self.add_button.set_sensitive(entry_valid)
        except TypeError:
            pass
    
    def set_busy(self):
        self.spinner.start()
        self.title_spinner.set_visible_child_name('spinner')
        self.set_sensitive(False)

    def show_error(self, exc):
        self.log.error(_('Could not add source: %s'), self.repo_entry.get_text())
        err_dialog = repo.get_error_messagedialog(
            self,
            _('Could not add source'),
            exc,
            _('{} could not be added').format(self.repo_entry.get_text())
        )
        err_dialog.run()
        err_dialog.destroy()

class DeleteDialog(Gtk.Dialog):

    ppa_name = False

    def __init__(self, parent, title, flatpak=False, refs=None):
        Gtk.Dialog.__init__(self, _('Remove {}').format(title), 
                            parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_REMOVE, Gtk.ResponseType.OK),
                             modal=1, use_header_bar=header)

        self.log = logging.getLogger("repoman.DeleteDialog")

        self.expanded_height = 400
        self.expanded_width = 200
        self.set_resizable(False)

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

        delete_label = Gtk.Label(
            _("Are you sure you want to remove this source?")
        )
        Gtk.StyleContext.add_class(delete_label.get_style_context(), "h2")
        content_grid.attach(delete_label, 1, 0, 1, 1)

        delete_explain = Gtk.Label.new(
            _(
                'If you remove this source, you will need to add it again '
                'to continue using it. Any software you\'ve installed from '
                'this source will remain installed.'
            )
        )

        if flatpak:
            delete_explain = Gtk.Label.new(
                _(
                    'If you remove this source, you will need to add it again '
                    'to continue using it.'
                )
            )
        delete_explain.props.wrap = True
        delete_explain.set_max_width_chars(50)
        delete_explain.set_xalign(0)
        content_grid.attach(delete_explain, 1, 1, 1, 1)

        remove_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        Gtk.StyleContext.add_class(
            remove_button.get_style_context(), "destructive-action"
        )

        self.show_all()

        if flatpak and refs:
            delete_explain_text = delete_explain.get_text()
            delete_explain_text += _(
                 ' All flatpaks you\'ve installed from this source will '
                 'be removed.'
            )
            delete_explain.set_text(delete_explain_text)

            removed_expander = Gtk.Expander.new(_('Removed Flatpaks'))
            removed_expander.connect('notify::expanded', self.show_hide_removed)
            content_grid.attach(removed_expander, 1, 2, 1, 1)

            self.removed_revealer = Gtk.Revealer()
            self.removed_revealer.set_margin_start(18)
            self.removed_revealer.set_transition_type(
                Gtk.RevealerTransitionType.CROSSFADE
            )
            content_grid.attach(self.removed_revealer, 1, 3, 1, 1)

            list_grid = Gtk.Grid()
            self.removed_revealer.add(list_grid)

            removed_label = Gtk.Label.new(
                _('The following Flatpaks will be removed with this source:')
            )
            list_grid.attach(removed_label, 0, 0, 1, 1)
            list_window = Gtk.ScrolledWindow()
            list_window.set_vexpand(True)
            list_window.set_hexpand(True)
            list_grid.attach(list_window, 0, 1, 1, 1)
            
            removed_view = Gtk.TextView()
            removed_view.set_editable(False)
            list_window.add(removed_view)

            removed_list = removed_view.get_buffer()
            removed_text = ''
            for ref in refs:
                if ref.get_appdata_name():
                    removed_text += f'{ref.get_appdata_name()} ({ref.get_name()})\n'
            for ref in refs:
                if not ref.get_appdata_name():
                    removed_text += f'{ref.get_name()}\n'
            removed_list.set_text(removed_text)
            
            self.show_all()
    
    def show_hide_removed(self, expander, data=None):
        self.removed_revealer.props.reveal_child = expander.get_expanded()
        if expander.get_expanded():
            self.resize(self.expanded_width, self.expanded_height)
            self.set_resizable(True)
        else:
            self.expanded_height = self.get_allocated_height() - 99
            self.expanded_width = self.get_allocated_width() - 52
            self.resize(self.expanded_width, 1)
            self.set_resizable(False)

class EditDialog(Gtk.Dialog):

    ppa_name = False

    def __init__(self, parent, source):
        self.log = logging.getLogger("repoman.EditDialog")
        
        self.source = source
        # Ensure the source is fully up to date.
        self.source.file.load()
        self.key = None
        has_key: bool = False
        supports_keys: bool = True
        try: 
            if self.source.get_key_info():
                has_key = True
        except AttributeError:
            # Repolib installed does not support keys
            supports_keys = False
        
        self.log.debug(
            'Repolib supports keys: %s / Source has key: %s', 
            supports_keys,
            has_key
        )
        

        Gtk.Dialog.__init__(self, _("Modify Source"), parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_SAVE, Gtk.ResponseType.OK),
                             modal=1, use_header_bar=header)


        self.parent = parent

        self.props.resizable = False
        self.props.width_request = 600

        content_area = self.get_content_area()

        self.content_stack = Gtk.Stack()
        self.content_stack.set_halign(Gtk.Align.START)
        content_area.add(self.content_stack)

        edit_grid = Gtk.Grid()
        edit_grid.set_margin_top(24)
        edit_grid.set_margin_left(24)
        edit_grid.set_margin_right(24)
        edit_grid.set_margin_bottom(24)
        edit_grid.set_column_spacing(12)
        edit_grid.set_row_spacing(12)
        edit_grid.set_halign(Gtk.Align.CENTER)
        self.content_stack.add_titled(edit_grid, 'edit', _('Modify Source'))

        key_grid = Gtk.Grid()
        key_grid.set_margin_top(24)
        key_grid.set_margin_left(24)
        key_grid.set_margin_right(24)
        key_grid.set_margin_bottom(24)
        key_grid.set_column_spacing(12)
        key_grid.set_row_spacing(12)
        key_grid.set_halign(Gtk.Align.START)
        self.content_stack.add_titled(key_grid, 'key', _('Signing Key Info'))

        if has_key:
            self.log.info('Adding Key Info Pane')
            stackswitcher = Gtk.StackSwitcher()
            stackswitcher.set_stack(self.content_stack)
            headerbar = self.get_titlebar()
            headerbar.set_custom_title(stackswitcher)
            stackswitcher.show()
        
        elif supports_keys:
            add_key_button = Gtk.Button.new_with_label(_('Add signing key'))
            edit_grid.attach(add_key_button, 1, 6, 1, 2)
            add_key_button.connect('clicked', self.on_add_key_clicked)

        name_label = Gtk.Label.new(_('Name'))
        name_label.set_halign(Gtk.Align.END)
        type_label = Gtk.Label(_("Source Code"))
        type_label.set_halign(Gtk.Align.END)
        uri_label = Gtk.Label(_("URIs"))
        uri_label.set_halign(Gtk.Align.END)
        version_label = Gtk.Label(_("Version"))
        version_label.set_halign(Gtk.Align.END)
        component_label = Gtk.Label(_("Components"))
        component_label.set_halign(Gtk.Align.END)
        enabled_label = Gtk.Label(_("Enabled"))
        enabled_label.set_halign(Gtk.Align.END)
        edit_grid.attach(name_label, 0, 0, 1, 1)
        edit_grid.attach(type_label, 0, 1, 1, 1)
        edit_grid.attach(uri_label, 0, 2, 1, 1)
        edit_grid.attach(version_label, 0, 3, 1, 1)
        edit_grid.attach(component_label, 0, 4, 1, 1)
        edit_grid.attach(enabled_label, 0, 5, 1, 1)

        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text(_('Name'))
        self.name_entry.set_text(self.source['X-Repolib-Name'])
        self.name_entry.set_activates_default(False)
        self.name_entry.set_width_chars(40)
        edit_grid.attach(self.name_entry, 1, 0, 1, 1)

        self.source_switch = Gtk.Switch()
        self.source_switch.set_halign(Gtk.Align.START)
        self.source_switch.set_active(self.source.sourcecode_enabled)
        self.source_switch.connect('state-set', self.on_source_switch_changed)
        edit_grid.attach(self.source_switch, 1, 1, 1, 1)

        self.uri_entry = Gtk.Entry()
        self.uri_entry.set_placeholder_text("https://ppa.launchpad.net/...")
        self.uri_entry.set_text(self.source['URIs'])
        self.uri_entry.set_activates_default(False)
        self.uri_entry.set_width_chars(40)
        edit_grid.attach(self.uri_entry, 1, 2, 1, 1)

        self.version_entry = Gtk.Entry()
        self.version_entry.set_placeholder_text(repo.get_os_codename())
        self.version_entry.set_text(self.source['Suites'])
        self.version_entry.set_activates_default(False)
        edit_grid.attach(self.version_entry, 1, 3, 1, 1)

        self.component_entry = Gtk.Entry()
        self.component_entry.set_placeholder_text("main")
        self.component_entry.set_text(self.source['Components'])
        self.component_entry.set_activates_default(False)
        edit_grid.attach(self.component_entry, 1, 4, 1, 1)

        self.enabled_switch = Gtk.Switch()
        self.enabled_switch.set_halign(Gtk.Align.START)
        self.enabled_switch.set_active(self.source.enabled.get_bool())
        self.enabled_switch.connect('state-set', self.on_enabled_switch_changed)
        edit_grid.attach(self.enabled_switch, 1, 5, 1, 1)

        if has_key:
            self.key = self.source.get_key_info()
            keyid_label = Gtk.Label.new(_('Key ID:'))
            keyid_label.set_halign(Gtk.Align.END)
            keyid_label.set_valign(Gtk.Align.START)
            fingerprint_label = Gtk.Label.new(_('Fingerprint:'))
            fingerprint_label.set_halign(Gtk.Align.END)
            keytype_label = Gtk.Label.new(_('Key Type:'))
            keytype_label.set_halign(Gtk.Align.END)
            issuedate_label = Gtk.Label.new(_('Issue Date:'))
            issuedate_label.set_halign(Gtk.Align.END)
            keysize_label = Gtk.Label.new(_('Size:'))
            keysize_label.set_halign(Gtk.Align.END)
            keypath_label = Gtk.Label.new(_('Keyring Path:'))
            keypath_label.set_halign(Gtk.Align.END)
            keypath_label.set_valign(Gtk.Align.START)
            delete_key_button = Gtk.Button.new_with_label(_('Remove Key'))
            delete_key_button.connect('clicked', self.on_delete_key_button_clicked)
            Gtk.StyleContext.add_class(
                delete_key_button.get_style_context(),
                'destructive-action'
            )
            key_grid.attach(keyid_label,       0, 0, 1, 1)
            key_grid.attach(fingerprint_label, 0, 1, 1, 1)
            key_grid.attach(keytype_label,     0, 2, 1, 1)
            key_grid.attach(issuedate_label,   0, 3, 1, 1)
            key_grid.attach(keysize_label,     0, 4, 1, 1)
            key_grid.attach(keypath_label,     0, 5, 1, 1)
            key_grid.attach(delete_key_button, 1, 6, 1, 1)
            keyid = Gtk.Label.new(self.key['uids'][0])
            keyid.set_selectable(True)
            keyid.set_line_wrap(True)
            keyid.set_max_width_chars(60)
            keyid.props.xalign = 0
            fingerprint = Gtk.Label.new(self.key['keyid'])
            fingerprint.set_selectable(True)
            if self.key['type'] == 'pub':
                keytype = Gtk.Label.new(_('Public'))
            else:
                keytype = Gtk.Label.new(_('Private'))
            keydate = date.fromtimestamp(int(self.key['date']))
            issuedate = Gtk.Label.new(keydate.ctime())
            issuedate.set_selectable(True)
            sizeunit:str = _('Bytes')
            keysize = Gtk.Label.new(f'{self.key["length"]} {sizeunit}')
            keysize.set_selectable(True)
            keypath = Gtk.Label.new(str(self.source.key.path))
            keypath.set_selectable(True)
            keypath.set_line_wrap(True)
            keypath.set_max_width_chars(60)
            keypath.props.xalign = 0
            for i in [keyid, fingerprint, keytype, issuedate, keysize, keypath]:
                i.set_halign(Gtk.Align.START)
            key_grid.attach(keyid,       1, 0, 1, 1)
            key_grid.attach(fingerprint, 1, 1, 1, 1)
            key_grid.attach(keytype,     1, 2, 1, 1)
            key_grid.attach(issuedate,   1, 3, 1, 1)
            key_grid.attach(keysize,     1, 4, 1, 1)
            key_grid.attach(keypath,     1, 5, 1, 1)



        save_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        cancel_button = self.get_widget_for_response(Gtk.ResponseType.CANCEL)

        Gtk.StyleContext.add_class(save_button.get_style_context(),
                                   "suggested-action")


        action_area = self.get_action_area()
        separator = Gtk.Box()
        separator.set_hexpand(True)
        action_area.add(separator)
        separator.show()
        separator2 = Gtk.Box()
        separator2.set_hexpand(True)
        action_area.add(separator2)
        separator2.show()
        action_area.props.layout_style = Gtk.ButtonBoxStyle.START

        self.show_all()

        if header == False:
            action_area.remove(save_button)
            action_area.remove(cancel_button)
            action_area.add(cancel_button)
            action_area.add(save_button)
    
    def on_add_key_clicked(self, button):
        """ button::clicked signal handler
        
        Open a dialog to add a signing key
        """
        dialog = AddKeyDialog(self, self.source)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                self.key = repo.get_key(
                    self.source,
                    key_type=dialog.key_type_combo.get_active_id(),
                    key_data=dialog.prime_buffer,
                    key_options=dialog.secondary_buffer
                )
            except Exception as err:
                self.log.error(
                    'Could not add key to %s: %s', 
                    self.source.ident, 
                    str(err)
                )
                error_dialog = repo.get_error_messagedialog(
                    self.parent,
                    f'Could not add key to {self.source.name}',
                    err,
                    f'{self.source.ident} will not be saved.'
                )
                error_dialog.run()
                error_dialog.destroy()
                dialog.destroy()
                self.response(Gtk.ResponseType.CANCEL)
            self.key_data = dialog.prime_buffer
            self.keytype = dialog.key_type_combo.get_active_id()
            dialog.destroy()
            if not self.key:
                raise Exception(f'Could not add the key to source {self.source.ident}!')
            self.response(Gtk.ResponseType.APPLY)
        dialog.destroy()
    
    def on_delete_key_button_clicked(self, button):
        delete_dialog = DeleteKeyDialog(self, self.source.ident)
        response = delete_dialog.run()
        delete_dialog.destroy()
        if response == Gtk.ResponseType.OK:
            self.response(Gtk.ResponseType.REJECT)
        

    def on_entry_changed(self, entry, prop):
        """ entry::changed signal handler

        We want to directly store the values of the entries in the source 
        object.

        Arguments:
            entry (Gtk.Editable): The Entry which was changed.
            prop: The property in which to store the data.
        """
        self.source[prop] = entry.get_text()
    
    def on_source_switch_changed(self, switch, state):
        """ switch::state-set handler for source code switch. """
        self.source.sourcecode_enabled = state
    
    def on_enabled_switch_changed(self, switch, state):
        """ switch::state-set handler for enabled switch. """
        self.source.enabled = state

class AddKeyDialog(Gtk.Dialog):

    def __init__(self, parent, source) -> None:
        self.log = logging.getLogger("repoman.EditDialog")
        self.source = source

        self.sks_keyserver = repo.repolib.key.SKS_KEYSERVER

        super().__init__(
            _("Add Signing Key"), parent, 0,
            (
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            ),
            modal=1, use_header_bar=header
        )

        self.parent = parent

        self.props.resizable = False
        self.props.width_request = 600

        content_area = self.get_content_area()

        content_grid = Gtk.Grid()
        content_grid.set_margin_top(24)
        content_grid.set_margin_left(24)
        content_grid.set_margin_right(24)
        content_grid.set_margin_bottom(24)
        content_grid.set_column_spacing(12)
        content_grid.set_row_spacing(12)
        content_area.add(content_grid)

        info_label = Gtk.Label.new(_(
            'Signing keys ensure system security by verifying that downloaded '
            'software from this source has not been tampered with.'
        ))
        info_label.set_justify(Gtk.Justification.CENTER)
        info_label.set_max_width_chars(60)
        info_label.set_line_wrap(True)
        info_label.set_hexpand(True)
        content_grid.attach(info_label, 0, 0, 2, 1)

        self.key_select_stack = Gtk.Stack()
        content_grid.attach(self.key_select_stack, 1, 1, 1, 2)
        self.sub_label = Gtk.Label.new(_('Select a thing'))
        self.sub_label.set_no_show_all(True)
        self.sub_label.set_valign(Gtk.Align.START)
        self.sub_label.set_halign(Gtk.Align.END)
        self.sub_label.set_vexpand(True)
        content_grid.attach(self.sub_label, 0, 2, 1, 1)

        self.prime_entry = Gtk.Entry()
        self.prime_entry.set_no_show_all(False)
        self.prime_buffer: str = ''

        self.secondary_entry = Gtk.Entry()
        self.secondary_entry.set_no_show_all(False)
        self.secondary_buffer: str = ''

        fingerprint_grid = Gtk.Grid()
        fingerprint_grid.set_row_spacing(5) # Aligns helper text with entry text
        self.key_select_stack.add_named(fingerprint_grid, 'fingerprint')
        fingerprint_entry = Gtk.Entry()
        fingerprint_entry.connect('changed', self.on_prime_entry_changed)
        fingerprint_entry.set_placeholder_text(_('Fingerprint'))
        fingerprint_entry.set_hexpand(True)
        fingerprint_grid.attach(fingerprint_entry, 0, 0, 1, 1)
        keyserver_entry = Gtk.Entry()
        keyserver_entry.connect('changed', self.on_secondary_entry_changed)
        keyserver_entry.set_placeholder_text(self.sks_keyserver)
        keyserver_entry.set_text(self.sks_keyserver)
        fingerprint_grid.attach(keyserver_entry, 0, 1, 1, 1)

        url_grid = Gtk.Grid()
        self.key_select_stack.add_named(url_grid, 'url')
        url_entry = Gtk.Entry()
        url_entry.connect('changed', self.on_prime_entry_changed)
        url_entry.set_hexpand(True)
        url_entry.set_placeholder_text(_('URL'))
        url_grid.attach(url_entry, 0, 0, 1, 1)

        path_grid = Gtk.Grid()
        self.key_select_stack.add_named(path_grid, 'path')

        path_select = Gtk.FileChooserButton(
            'Signing Key Path',
            Gtk.FileChooserAction.OPEN
        )
        path_select.set_current_folder(str(repo.repolib.KEYS_DIR))
        path_select.set_hexpand(True)
        path_select.connect('file-set', self.on_file_set)
        path_grid.attach(path_select, 0, 0, 1, 1)

        ascii_grid = Gtk.Grid()
        self.key_select_stack.add_named(ascii_grid, 'ascii')
        ascii_scrolled = Gtk.ScrolledWindow()
        ascii_textview = Gtk.TextView()
        ascii_textview.get_buffer().connect('changed', self.on_prime_entry_changed)
        ascii_textview.set_hexpand(True)
        ascii_textview.set_vexpand(True)
        ascii_textview.set_monospace(True)
        ascii_grid.attach(ascii_scrolled, 0, 1, 1, 1)
        ascii_scrolled.add(ascii_textview)

        self.key_type_combo = Gtk.ComboBoxText()
        self.key_type_combo.set_valign(Gtk.Align.START)
        self.key_type_combo.append('fingerprint', _('Fingerprint'))
        self.key_type_combo.append('url', _('URL'))
        self.key_type_combo.append('path', _('Path'))
        self.key_type_combo.append('ascii', _('ASCII-Armor'))
        self.key_type_combo.connect('changed', self.on_key_type_changed)
        content_grid.attach(self.key_type_combo, 0, 1, 1, 1)

        self.save_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        Gtk.StyleContext.add_class(self.save_button.get_style_context(),
                                   "suggested-action")
        self.save_button.set_sensitive(False)

        self.show_all()
        self.key_type_combo.set_active_id('fingerprint')


    def on_file_set(self, button):
        self.prime_buffer = button.get_filename()
        self.log.debug('Prime buffer: %s', self.prime_buffer)
        self.save_button.set_sensitive(True)

    def on_prime_entry_changed(self, entry):
        """entry::changed signal handler
        
        Puts the contents of the entry into the primary buffer.
        """
        try:
            # widget is an entry
            self.prime_buffer = entry.get_text()
        except TypeError:
            # Widget is a TextBuffer
            self.prime_buffer = entry.props.text
        
        if len(self.prime_buffer) > 0:
            self.save_button.set_sensitive(True)
        else:
            self.save_button.set_sensitive(False)
        self.log.debug('Prime buffer:')
        self.log.debug(self.prime_buffer)
    
    def on_secondary_entry_changed(self, entry):
        """entry::changed signal handler
        
        Puts the contents of the entry into the secondary buffer.
        """
        self.secondary_buffer = entry.get_text()
        self.log.debug('Secondary buffer:')
        self.log.debug(self.secondary_buffer)
    
    def on_key_type_changed(self, combo):
        """ComboBox::changed signal handler
        
        Need to show/hide and set text for the sub label
        """
        self.save_button.set_sensitive(False)
        self.prime_buffer = ''
        self.secondary_buffer = ''
        sub_label_props = {
           #'combo-id':    (_('Text to set'), visible:bool)
            'fingerprint': (_('Keyserver'),   True),
            'url':         (_('none'),        False),
            'path':        (_('none'),        False),
            'ascii':       (_('none'),        False)
        }
        self.log.debug('Key Type: %s', combo.get_active_id())
        props_to_set = sub_label_props[combo.get_active_id()]
        self.sub_label.set_text(props_to_set[0])
        self.sub_label.set_visible(props_to_set[1])
        self.key_select_stack.set_visible_child_name(combo.get_active_id())

class DeleteKeyDialog(Gtk.Dialog):

    def __init__(self, parent, name) -> None:
        super().__init__(
            'Remove Signing Key',
            parent,
            0,
            ((
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_DELETE, Gtk.ResponseType.OK
            )),
            modal=1,
            use_header_bar=header
        )
        self.set_size_request(350, 250)
        self.set_resizable(False)
        self.set_deletable(False)
        self.set_transient_for(parent)

        content_area = self.get_content_area()

        content_grid = Gtk.Grid()
        content_grid.set_margin_top(24)
        content_grid.set_margin_left(24)
        content_grid.set_margin_right(24)
        content_grid.set_margin_bottom(24)
        content_grid.set_column_spacing(36)
        content_grid.set_row_spacing(12)
        content_area.add(content_grid)

        main_text:str = _(
            f'<b>Remove signing key for {name}</b>'
        )
        main_label = Gtk.Label()
        main_label.set_width_chars(55)
        main_label.set_max_width_chars(55)
        main_label.set_line_wrap(True)
        main_label.set_markup(main_text)

        sub_text:str = _(
            'If you remove the key, there may no longer be any verification of '
            'software packages from this repository, including for future '
            'updates. This may cause errors with your updates.\n\n'
            'If no other sources use this key, it will be deleted from '
            'this computer.'
        )
        sub_label = Gtk.Label.new(sub_text)
        sub_label.set_width_chars(55)
        sub_label.set_max_width_chars(55)
        sub_label.set_line_wrap(True)
        
        content_grid.attach(main_label, 0, 0, 1, 1)
        content_grid.attach(sub_label, 0, 1, 1, 1)

        cancel_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        Gtk.StyleContext.add_class(
            cancel_button.get_style_context(),
            'destructive-action'
        )

        self.show_all()
       
class InfoDialog(Gtk.Dialog):

    def __init__(self, parent, name, option):
        self.installation = flatpak_helper.get_installation_for_type(option)
        
        self.remote = self.installation.get_remote_by_name(name, None)

        if self.remote.get_title():
            title = self.remote.get_title()
        else:
            title = name
        name = self.remote.get_name()
        description = name
        if self.remote.get_comment():
            description = self.remote.get_comment()
        if self.remote.get_description():
            description = self.remote.get_description()
        url = self.remote.get_homepage()

        settings = Gtk.Settings.get_default()
        header = settings.props.gtk_dialogs_use_header
        super().__init__(
            f'{title}',
            parent, 
            0,
            modal=1,
            use_header_bar=header
        )
        self.log = logging.getLogger(f'repoman.info-{name}')

        self.expanded_height = 350
        self.expanded_width = 350
        self.set_default_size(350, 350)

        content_area = self.get_content_area()
        headerbar = self.get_header_bar()

        disable_switch = Gtk.Switch()
        disable_switch.set_active(not self.remote.get_disabled())
        disable_switch.connect('state-set', self.on_switch_toggled)
        headerbar.pack_end(disable_switch)

        content_grid = Gtk.Grid()
        content_grid.set_halign(Gtk.Align.FILL)
        content_grid.set_margin_top(24)
        content_grid.set_margin_bottom(24)
        content_grid.set_margin_start(24)
        content_grid.set_margin_end(24)
        content_grid.set_column_spacing(12)
        content_grid.set_row_spacing(6)
        content_area.add(content_grid)

        self.icon_box = Gtk.Box()
        self.icon_box.set_halign(Gtk.Align.CENTER)
        content_grid.attach(self.icon_box, 0, 0, 1, 1)

        self.log.debug('Trying to get icon for %s', name)
        cached_icon = flatpak_helper.get_icon_cache_for_remote(name, option)
        pixbuf = flatpak_helper.get_icon_pixbuf(cached_icon)
        
        if pixbuf:
            self.icon = flatpak_helper.get_image_from_pixbuf(pixbuf)
            self.icon_box.add(self.icon)
        else:
            self.icon = Gtk.Image.new_from_icon_name(
                'notfound',
                Gtk.IconSize.SMALL_TOOLBAR
            )
            self.icon.props.opacity = 0

        title_label = Gtk.Label()
        title_label.set_line_wrap(True)
        title_label.set_markup(f'<b>{title}</b>')
        content_grid.attach(title_label, 0, 1, 1, 1)

        name_label = Gtk.Label()
        name_label.set_markup(f'<i><small>{name}</small></i>')
        content_grid.attach(name_label, 0, 2, 1, 1)

        description_label = Gtk.Label()
        description_label.set_hexpand(True)
        description_label.set_margin_top(18)
        description_label.set_margin_bottom(12)
        description_label.set_line_wrap(True)
        description_label.set_max_width_chars(36)
        description_label.set_width_chars(36)
        description_label.set_text(description)
        content_grid.attach(description_label, 0, 3, 1, 1)
        
        if url:
            url_button = Gtk.LinkButton.new_with_label(_('Homepage'))
            url_button.set_uri(url)
            content_grid.attach(url_button, 0, 4, 1, 1)
        
        installed_refs = flatpak_helper.get_installed_refs_from_remote(
            name, option
        )
        if installed_refs:
            refs_expander = Gtk.Expander.new(_('Installed Flatpaks'))
            refs_expander.connect('notify::expanded', self.show_hide_removed)
            content_grid.attach(refs_expander, 0, 5, 1, 1)

            self.refs_revealer = Gtk.Revealer()
            self.refs_revealer.set_margin_start(18)
            self.refs_revealer.set_hexpand(True)
            self.refs_revealer.set_transition_type(
                Gtk.RevealerTransitionType.CROSSFADE
            )
            content_grid.attach(self.refs_revealer, 0, 6, 1, 1)

            list_grid = Gtk.Grid()
            self.refs_revealer.add(list_grid)

            installed_label = Gtk.Label.new(
                _('The following Flatpaks are currently installed from {}').format(title)
            )

            installed_label.set_line_wrap(True)
            list_grid.attach(installed_label, 0, 0, 1, 1)
            list_window = Gtk.ScrolledWindow()
            list_window.set_vexpand(True)
            list_window.set_hexpand(True)
            list_grid.attach(list_window, 0, 1, 1, 1)
            
            refs_view = Gtk.TextView()
            refs_view.set_editable(False)
            list_window.add(refs_view)

            refs_buff = refs_view.get_buffer()
            refs_list = _('Applications:')
            refs_list += '\n'
            for ref in installed_refs:
                if ref.get_kind() == flatpak_helper.Flatpak.RefKind.APP:
                    if ref.get_appdata_name():
                        refs_list += f'{ref.get_appdata_name()}\n'
                    else: 
                        refs_list += f'{ref.get_name()}\n'
            
            refs_list += '\nRuntimes:\n'
            for ref in installed_refs:
                if ref.get_kind() == flatpak_helper.Flatpak.RefKind.RUNTIME:
                    refs_list += f'{ref.get_name()}\n'
            refs_buff.set_text(refs_list)

        self.show_all()

        icon_thread = flatpak_helper.IconThread(self, name, option)
        icon_thread.start()
    
    def set_remote_icon(self, image):
        """ Set's the remote icon to a given Gtk.Image

        Arguments:
            image (`Gtk.Image`): The image to set.
        """
        self.icon.destroy()
        self.icon = image
        self.icon.show()
        self.icon_box.add(self.icon)
        self.log.debug('Got latest icon')    

    def show_hide_removed(self, expander, data=None):
        self.refs_revealer.props.reveal_child = expander.get_expanded()
        if expander.get_expanded():
            self.resize(self.expanded_width, self.expanded_height)
        else:
            self.expanded_height = self.get_allocated_height() - 99
            self.expanded_width = self.get_allocated_width() - 52
            self.resize(self.expanded_width, 1)
        
    def on_switch_toggled(self, switch, state):
        self.log.debug('Setting disabled to %s', not state)
        self.remote.set_disabled(not state)
        self.installation.modify_remote(self.remote)
