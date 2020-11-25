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
from gi.repository import Gtk, Gio
from . import repo
from gettext import gettext as _

prime_pos = Gtk.EntryIconPosition.PRIMARY
sec_pos = Gtk.EntryIconPosition.SECONDARY

class Settings(Gtk.Box):
    repo_descriptions = {
        'universe': _('Community-maintained software'),
        'restricted': _('Proprietary drivers for devices'),
        'multiverse': _('Software with Copyright or Legal Restrictions')
    }

    def __init__(self, parent):
        Gtk.Box.__init__(self, False, 0)

        self.system_repo = parent.system_repo
        self.log = logging.getLogger('repoman.Settings')
        self.log.debug('Logging established.')
        self.os_name = repo.get_os_name()
        self.handlers = {}
        self.prev_enabled = False
        self.proposed_name = f'{repo.get_os_codename()}-proposed'

        self.parent = parent

        self.source_check = self.get_new_switch(
            'source-code',
            _('Include source code')
        )
        self.handlers[self.source_check.toggle] = self.source_check.toggle.connect(
            'state-set',
            self.on_source_check_toggled
        )
        self.proposed_check = self.get_new_switch(
           self.proposed_name,
            _('Prerelease updates')
        )
        self.handlers[self.proposed_check.toggle] = self.proposed_check.toggle.connect(
            'state-set',
            self.on_proposed_check_toggled
        )

        source_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        source_box.set_hexpand(True)
        source_label = Gtk.Label.new(_('Include source code'))
        source_label.set_halign(Gtk.Align.START)
        source_box.add(source_label)
        source_switch = Gtk.Switch()
        source_switch.suite = f'{repo.get_os_codename()}-proposed'
        source_switch.set_halign(Gtk.Align.END)

        settings_grid = Gtk.Grid()
        settings_grid.set_margin_left(36)
        settings_grid.set_margin_top(24)
        settings_grid.set_margin_right(36)
        settings_grid.set_margin_bottom(12)
        settings_grid.set_hexpand(True)
        settings_grid.set_halign(Gtk.Align.CENTER)
        self.add(settings_grid)

        sources_title = Gtk.Label(_('Official Sources'))
        sources_title.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(sources_title.get_style_context(), 'h2')
        settings_grid.attach(sources_title, 0, 0, 1, 1)

        sources_label = Gtk.Label.new(
            # Can't seem to use Fstrings with gettext
            _("Official sources are provided by {} "
              "and its developers. It's recommended to leave these "
              "sources enabled.").format(self.os_name)
        )
        sources_label.set_line_wrap(True)
        sources_label.set_justify(Gtk.Justification.FILL)
        sources_label.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(
            sources_label.get_style_context(),
            'description'
        )
        settings_grid.attach(sources_label, 0, 1, 1, 1)

        self.mirror_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        Gtk.StyleContext.add_class(self.mirror_box.get_style_context(), 'linked')
        settings_grid.attach(self.mirror_box, 0, 2, 1, 1)

        if self.system_repo:
            if self.system_repo.default_mirror:
                self.reset_mirrors_button = Gtk.Button()
                self.reset_mirrors_button.set_label(_('Reset Mirrors to Defaults'))
                self.reset_mirrors_button.set_halign(Gtk.Align.END)
                self.reset_mirrors_button.set_margin_top(6)
                Gtk.StyleContext.add_class(
                    self.reset_mirrors_button.get_style_context(),
                    'destructive-action'
                )
                self.reset_mirrors_button.connect(
                    'clicked',
                    self.on_reset_mirror_button_clicked
                )
                settings_grid.attach(self.reset_mirrors_button, 0, 3, 1, 1)

        self.checks_grid = Gtk.VBox()
        self.checks_grid.set_margin_left(12)
        self.checks_grid.set_margin_top(24)
        self.checks_grid.set_margin_right(12)
        self.checks_grid.set_margin_bottom(12)
        self.checks_grid.set_spacing(12)
        settings_grid.attach(self.checks_grid, 0, 4, 1, 1)

        developer_options = Gtk.Expander()
        developer_options.set_label(_('Developer Options (Advanced)'))
        settings_grid.attach(developer_options, 0, 5, 1, 1)

        self.developer_grid = Gtk.VBox()
        self.developer_grid.set_margin_left(12)
        self.developer_grid.set_margin_top(12)
        self.developer_grid.set_margin_right(36)
        self.developer_grid.set_margin_bottom(12)
        self.developer_grid.set_spacing(12)
        developer_options.add(self.developer_grid)

        developer_label = Gtk.Label.new(
            _('These options are primarily of interest to developers.')
        )
        developer_label.set_line_wrap(True)
        developer_label.set_halign(Gtk.Align.START)
        developer_label.set_margin_start(0)
        self.developer_grid.add(developer_label)
        self.developer_grid.add(self.source_check)
        self.developer_grid.add(self.proposed_check)

        self.create_switches()
        if self.system_repo:
            self.on_config_changed(None, None, None, None)
            developer_options.grab_default()
            developer_options.grab_focus()
        else:
            self.switches_sensitive = False

        # Watch the config directory for changes, so we can reload if so
        self.file = Gio.File.new_for_path('/etc/apt/sources.list.d/')
        self.monitor = self.file.monitor_directory(Gio.FileMonitorFlags.NONE)
        self.monitor.connect('changed', self.on_config_changed)
        self.log.debug('Monitor Created: %s', self.monitor)
        self.show_all()

    @property
    def checks_enabled(self):
        """ bool: whether the checks/switches are enabled or not. """
        for checkbox in self.checks_grid.get_children():
            if checkbox.toggle.get_active():
                return True
            else:
                continue
        return False

    @property
    def switches_sensitive(self):
        for switchbox in self.checks_grid.get_children():
            if switchbox.get_sensitive():
                return True
            else:
                continue
        return False

    @switches_sensitive.setter
    def switches_sensitive(self, sensitive):
        for switchbox in self.checks_grid.get_children():
            switchbox.set_sensitive(sensitive)
        for switchbox in self.developer_grid.get_children():
            switchbox.set_sensitive(sensitive)

    def block_handlers(self):
        for widget in self.handlers:
            if widget.handler_is_connected(self.handlers[widget]):
                widget.handler_block(self.handlers[widget])

    def unblock_handlers(self):
        for widget in self.handlers:
            if widget.handler_is_connected(self.handlers[widget]):
                widget.handler_unblock(self.handlers[widget])

    def get_mirror_entry(
            self,
            uri=None,
            placeholder='http://example.com/ubuntu',
            icon_name='edit-delete-symbolic',
            icon_tooltip=_('Remove Mirror'),
            icon_position=Gtk.EntryIconPosition.SECONDARY
        ):
        self.log.debug('Creating entry for %s', uri)
        mirror_entry = Gtk.Entry()
        mirror_entry.set_input_purpose(Gtk.InputPurpose.URL)
        mirror_entry.set_placeholder_text(placeholder)
        if uri:
            mirror_entry.set_text(uri)
        mirror_entry.uri = uri
        mirror_entry.handlers = {}

        mirror_entry.set_icon_from_icon_name(icon_position, icon_name)
        mirror_entry.set_icon_sensitive(icon_position, True)
        mirror_entry.set_icon_activatable(icon_position, True)
        mirror_entry.set_icon_tooltip_text(icon_position, icon_tooltip)
        return mirror_entry

    def set_mirrors(self):
        """ Sets up the list of mirrors.

        Also adds a blank entry for adding a new mirror to the list.
        """
        self.system_repo.load_from_file()
        self.log.debug('Adding mirrors')
        for child in self.mirror_box.get_children():
            self.log.debug('Removing outdated entry for %s', child.get_text())
            child.destroy()

        new_mirror_entry = self.get_mirror_entry(
            placeholder=_('Add a new mirror'),
            icon_name='list-add-symbolic',
            icon_tooltip=_('Add mirror')
        )
        for signal in ['icon-release', 'activate']:
            new_mirror_entry.connect(signal, self.do_entry_add)
        new_mirror_entry.set_icon_from_icon_name(prime_pos, '')
        self.mirror_box.pack_end(new_mirror_entry, True, True, 0)
        new_mirror_entry.connect('changed', self.do_new_entry_changed)
        new_mirror_entry.show()

        for uri in self.system_repo.uris:
            self.log.debug('Mirror found: %s', uri)
            mirror_entry = self.get_mirror_entry(uri=uri)
            mirror_entry.connect('icon-release', self.do_entry_delete)
            mirror_entry.connect('activate', self.do_entry_delete)
            mirror_entry.connect('changed', self.do_entry_changed)
            if len(self.system_repo.uris) == 1:
                # Don't allow removing the last mirror
                self.log.debug('Mirror %s is the only mirror', uri)
                mirror_entry.set_icon_from_icon_name(sec_pos, '')
            self.mirror_box.pack_start(mirror_entry, True, True, 0)
            mirror_entry.show()
        
        if self.system_repo.default_mirror:
            if [self.system_repo.default_mirror] == self.system_repo.uris:
                self.reset_mirrors_button.set_sensitive(False)
            else:
                self.reset_mirrors_button.set_sensitive(True)

    def do_entry_add(self, entry, *args, **kwargs):
        """ :icon-release: signal handler for the new_mirror_entry."""
        if entry.get_icon_name(prime_pos) == 'selection-checked-symbolic':
            new_uri = entry.get_text()
            uris = self.system_repo.uris
            if not new_uri in uris:
                uris.append(new_uri)
            try:
                self.system_repo.uris = uris
                self.system_repo.save_to_disk()
            except Exception as err:
                self.log.error(
                    'Could not add mirror %s: %s', new_uri, str(err)
                )
                err_dialog = repo.get_error_messagedialog(
                    self.parent.parent,
                    f'Could not add URI',
                    err,
                    f'{new_uri} could not be added to the system mirrors'
                )
                err_dialog.run()
                err_dialog.destroy()
    
    def do_new_entry_changed(self, entry):
        """ :changed: signal handler for the new-mirror entry."""
        if entry.get_text():
            if repo.url_validator(entry.get_text()):
                entry.set_icon_from_icon_name(prime_pos, 'selection-checked-symbolic')
                entry.set_icon_sensitive(sec_pos, True)
                entry.set_icon_activatable(sec_pos, True)
            else:
                entry.set_icon_from_icon_name(prime_pos, 'dialog-error-symbolic')
                entry.set_icon_sensitive(sec_pos, False)
                entry.set_icon_activatable(sec_pos, False)
        else:
            entry.set_icon_from_icon_name(prime_pos, '')

    def do_entry_changed(self, entry):
        """ :changed: signal handler for mirror_entry items. """
        if entry.get_text() != entry.uri:
            entry.set_icon_from_icon_name(sec_pos, 'document-save-symbolic')
        else:
            if len(self.system_repo.uris) == 1:
                entry.set_icon_from_icon_name(sec_pos, '')
            else:
                entry.set_icon_from_icon_name(sec_pos, 'edit-delete-symbolic')

    def do_entry_delete(self, entry, *args, **kwargs):
        """ :icon-release: handler for mirror_entry items.

        Used to remove existing entries from the list.
        """
        uris = self.system_repo.uris
        if entry.get_icon_name(sec_pos):
            if entry.uri in self.system_repo.uris:
                uris.remove(entry.uri)

            new_entry = not entry.get_text() in self.system_repo.uris
            action_edit = entry.get_icon_name(sec_pos) == 'document-save-symbolic'
            if new_entry and action_edit:
                uris.append(entry.get_text())

            try:
                self.system_repo.uris = uris
                self.system_repo.save_to_disk()
            except Exception as err:
                self.log.error(
                    'Could not remove mirror %s: %s', entry.uri, str(err)
                )
                err_dialog = repo.get_error_messagedialog(
                    self.parent.parent,
                    f'Could not remove mirror',
                    err,
                    f'The mirror {entry.uri} could not be removed'
                )
                err_dialog.run()
                err_dialog.destroy()


    def get_new_switch(self, component, description=None):
        """ Creates a Box with a new switch and a description.

        If the name of the component matches one of the normal default
        components, include the description of the component. Otherwise use the
        supplied description (if given) or the name of the component.

        Arguments:
            component (str): The name of a component to bind to the switch
            description (str): An optional description to use if the component
                isn't of the predefinied normal sources.

        Returns:
            A Gtk.Box with the added switch and label description
        """

        switch = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        switch.set_hexpand(True)
        if component in self.repo_descriptions:
            description = self.repo_descriptions[component]

        label_text = component
        if description:
            label_text = f'{description} ({component})'
        label = Gtk.Label.new(label_text)
        label.set_halign(Gtk.Align.START)
        switch.label = label
        switch.add(label)
        toggle = Gtk.Switch()
        toggle.set_halign(Gtk.Align.END)
        toggle.set_hexpand(True)
        toggle.component = switch.component = component
        switch.toggle = toggle
        switch.add(toggle)

        switch.show_all()
        return switch

    def create_switches(self):
        """ Create the grid of switches that control the sources. """
        for switch in self.checks_grid.get_children():
            self.checks_grid.remove(switch)

        for component in self.repo_descriptions:
            switch = self.get_new_switch(component)
            self.handlers[switch.toggle] = switch.toggle.connect(
                'state-set',
                self.on_component_toggled
            )
            switch.show()
            self.checks_grid.add(switch)

        if self.system_repo:
            for component in self.system_repo.components:
                if component in self.repo_descriptions:
                    continue
                if component == 'main':
                    # Doesn't really make sense for this to be toggleable.
                    continue
                switch = self.get_new_switch(component)
                self.handlers[switch.toggle] = switch.toggle.connect(
                    'state-set',
                    self.on_component_toggled
                )
                switch.show()
                self.checks_grid.add(switch)

    def set_child_checks_sensitive(self):
        self.source_check.set_sensitive(self.prev_enabled)
        self.proposed_check.set_sensitive(self.prev_enabled)
        try:
            self.parent.updates.set_checks_enabled(self.prev_enabled)
        except AttributeError:
            # In case the updates page hasn't been init'd yet
            pass

    def show_source_code(self):
        self.system_repo.load_from_file()
        self.block_handlers()
        self.source_check.toggle.set_active(self.system_repo.source_code_enabled)
        self.unblock_handlers()

    def show_proposed(self):
        self.system_repo.load_from_file()
        self.block_handlers()
        if self.proposed_name in self.system_repo.suites:
            self.proposed_check.toggle.set_active(True)
        else:
            self.proposed_check.toggle.set_active(False)
        self.unblock_handlers()

    def show_distro(self):
        self.system_repo.load_from_file()
        self.create_switches()
        self.block_handlers()
        self.switches_sensitive = False
        if self.system_repo:
            self.switches_sensitive = True
            for comp in self.checks_grid.get_children():
                if comp.component in self.system_repo.components:
                    self.log.debug('Component %s is enabled', comp.component)
                    comp.toggle.set_active(True)
                else:
                    self.log.debug('Component %s is disabled', comp.component)
                    comp.toggle.set_active(False)

        self.unblock_handlers()

    def on_component_toggled(self, switch, state):
        self.system_repo.set_component_enabled(
            component=switch.component, enabled=state
        )

    def on_source_check_toggled(self, switch, state):
        self.system_repo['Types'] = 'deb'
        if state:
            self.system_repo['Types'] = 'deb deb-src'
        try:
            self.system_repo.save_to_disk()
        except Exception as err:
            self.log.error(
                    'Could not set source code: %s', str(err)
            )
            err_dialog = repo.get_error_messagedialog(
                self.parent.parent,
                f'Could not set Source Code',
                err,
                'The system source code status could not be changed'
            )
            err_dialog.run()
            err_dialog.destroy()

    def on_proposed_check_toggled(self, switch, state):
        self.system_repo.set_suite_enabled(
            suite=switch.component, enabled=state
        )

    def on_config_changed(self, monitor, file, other_file, event_type):
        self.log.debug('Installation changed, regenerating list')
        if self.system_repo:
            self.show_distro()
            self.show_source_code()
            self.show_proposed()
            self.set_mirrors()

    def on_reset_mirror_button_clicked(self, button):
        self.log.warning('Resetting mirrors to default values.')
        try:
            self.system_repo.set_default_mirror()
            self.system_repo.save_to_disk()
        except Exception as err:
            self.log.error(
                'Could not reset mirrors'
            )
            err_dialog = repo.get_error_messagedialog(
                self.parent.parent,
                f'Could not reset the system mirrors',
                err,
                'The system mirrors could not be reset'
            )
            err_dialog.run()
            err_dialog.destroy()
