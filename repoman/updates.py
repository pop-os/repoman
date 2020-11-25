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
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
from gettext import gettext as _

from . import repo

class Updates(Gtk.Box):

    distro_codename = repo.get_os_codename()
    os_name = repo.get_os_name()
    repo_descriptions = {
        f'{distro_codename}-security': _('Important security updates'),
        f'{distro_codename}-updates': _('Recommended updates'),
        f'{distro_codename}-backports': _('Unsupported updates')
    }

    def __init__(self, parent):
        Gtk.Box.__init__(self, False, 0)

        self.log = logging.getLogger("repoman.Updates")
        self.log.debug('Logging established')

        self.parent = parent
        self.system_repo = parent.system_repo
        self.handlers = {}

        updates_grid = Gtk.Grid()
        updates_grid.set_margin_left(12)
        updates_grid.set_margin_top(24)
        updates_grid.set_margin_right(12)
        updates_grid.set_margin_bottom(12)
        updates_grid.set_hexpand(True)
        updates_grid.set_halign(Gtk.Align.CENTER)
        self.add(updates_grid)

        updates_title = Gtk.Label(_("Update Sources"))
        updates_title.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(updates_title.get_style_context(), "h2")
        updates_grid.attach(updates_title, 0, 0, 1, 1)

        updates_label = Gtk.Label(_("These sources control how %s checks for updates. It is recommended to leave these sources enabled.") % self.os_name)
        updates_label.set_line_wrap(True)
        updates_label.set_justify(Gtk.Justification.FILL)
        updates_label.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(updates_label.get_style_context(), "description")
        updates_grid.attach(updates_label, 0, 1, 1, 1)

        self.checks_grid = Gtk.VBox()
        self.checks_grid.set_margin_left(12)
        self.checks_grid.set_margin_top(24)
        self.checks_grid.set_margin_right(12)
        self.checks_grid.set_margin_bottom(12)
        self.checks_grid.set_spacing(12)
        updates_grid.attach(self.checks_grid, 0, 2, 1, 1)
        self.checks_grid.show()

        self.create_switches()
        self.set_suites_enabled(self.parent.setting.checks_enabled)
        if self.system_repo:
            self.show_updates()
        
        # Watch the config directory for changes, so we can reload if so
        self.file = Gio.File.new_for_path('/etc/apt/sources.list.d/')
        self.monitor = self.file.monitor_directory(Gio.FileMonitorFlags.NONE)
        self.monitor.connect('changed', self.on_config_changed)
        self.log.debug('Monitor Created: %s', self.monitor)
        self.show_all()

    def block_handlers(self):
        for widget in self.handlers:
            if widget.handler_is_connected(self.handlers[widget]):
                widget.handler_block(self.handlers[widget])

    def unblock_handlers(self):
        for widget in self.handlers:
            if widget.handler_is_connected(self.handlers[widget]):
                widget.handler_unblock(self.handlers[widget])

    def get_new_switch(self, suite, description=None):
        """ Creates a Box with a new switch and a description.

        If the name of the suite matches one of the normal default
        suites, include the description of the suite. Otherwise use the
        supplied description (if given) or the name of the suite.

        Arguments:
            suite (str): The name of a distro suite to bind to the switch
            description (str): An optional description to use if the suite
                isn't of the predefinied normal sources.

        Returns:
            A Gtk.Box with the added switch and label description
        """

        switch = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        switch.set_hexpand(True)
        if suite in self.repo_descriptions:
            description = self.repo_descriptions[suite]

        label_text = suite
        if description:
            label_text = f'{description} ({suite})'
        label = Gtk.Label.new(label_text)
        label.set_halign(Gtk.Align.START)
        switch.label = label
        switch.add(label)
        toggle = Gtk.Switch()
        toggle.set_halign(Gtk.Align.END)
        toggle.set_hexpand(True)
        toggle.suite = switch.suite = suite
        switch.toggle = toggle
        switch.add(toggle)

        return switch

    def create_switches(self):
        """ Create switches for all of the suites which can be toggled. """
        for switch in self.checks_grid.get_children():
            self.checks_grid.remove(switch)

        for repo in self.repo_descriptions:
            switch = self.get_new_switch(repo)

            self.handlers[switch.toggle] = switch.toggle.connect(
                'state-set',
                self.on_suite_toggled
            )
            self.checks_grid.add(switch)
            switch.show_all()
        
        if self.system_repo:
            for suite in self.system_repo.suites:
                if suite in self.repo_descriptions:
                    continue
                if 'proposed' in suite:
                    # This is handled on the settings page.
                    continue
                if self.distro_codename == suite:
                    # Skip the standard distro suite.
                    continue
                switch = self.get_new_switch(suite)
                self.handlers[switch.toggle] = switch.toggle.connect(
                    'state-set',
                    self.on_suite_toggled
                )
                self.checks_grid.add(switch)
                switch.show_all()

    def show_updates(self):
        """ Initialize the state of all of the switches. """
        self.log.debug("init_distro")
        self.system_repo.load_from_file()
        self.create_switches()
        self.block_handlers()
        
        for suite in self.checks_grid.get_children():
            if suite.suite in self.system_repo.suites:
                suite.toggle.set_active(True)
            else:
                suite.toggle.set_active(False)
            
        self.unblock_handlers()

    def set_suites_enabled(self, enabled):
        for suite in self.checks_grid.get_children():
            suite.set_sensitive(enabled)

    def on_suite_toggled(self, switch, state):
        """ state-set handler for suite switches. """
        self.system_repo.set_suite_enabled(suite=switch.suite, enabled=state)

    def on_config_changed(self, monitor, file, other_file, event_type):
        self.log.debug('Installation changed, regenerating list')
        if self.system_repo:
            self.show_updates()
            self.set_suites_enabled(self.parent.setting.checks_enabled)
