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
import gi
import logging
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from .ppa import PPA
import gettext
gettext.bindtextdomain('repoman', '/usr/share/repoman/po')
gettext.textdomain("repoman")
_ = gettext.gettext

class Settings(Gtk.Box):
    
    def __init__(self, parent):
        Gtk.Box.__init__(self, False, 0)

        self.ppa = PPA(self)
        self.log = logging.getLogger('repoman.Settings')
        self.log.debug('Logging established.')
        self.os_name = self.ppa.get_os_name()
        self.handlers = {}

        self.parent = parent

        self.source_check = Gtk.CheckButton(label=_("Include source code"))
        self.proposed_check = Gtk.CheckButton()

        settings_grid = Gtk.Grid()
        settings_grid.set_margin_left(12)
        settings_grid.set_margin_top(24)
        settings_grid.set_margin_right(12)
        settings_grid.set_margin_bottom(12)
        settings_grid.set_hexpand(True)
        settings_grid.set_halign(Gtk.Align.CENTER)
        self.add(settings_grid)

        sources_title = Gtk.Label(_("Official Sources"))
        sources_title.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(sources_title.get_style_context(), "h2")
        settings_grid.attach(sources_title, 0, 0, 1, 1)

        sources_label = Gtk.Label(_("Official sources are provided by %s and its developers. It's recommended to leave these sources enabled.") % self.os_name)
        sources_label.set_line_wrap(True)
        sources_label.set_justify(Gtk.Justification.FILL)
        sources_label.set_halign(Gtk.Align.START)
        Gtk.StyleContext.add_class(sources_label.get_style_context(), "description")
        settings_grid.attach(sources_label, 0, 1, 1, 1)

        self.checks_grid = Gtk.VBox()
        self.checks_grid.set_margin_left(12)
        self.checks_grid.set_margin_top(24)
        self.checks_grid.set_margin_right(12)
        self.checks_grid.set_margin_bottom(12)
        self.checks_grid.set_spacing(12)
        settings_grid.attach(self.checks_grid, 0, 2, 1, 1)

        developer_options = Gtk.Expander()
        developer_options.set_label(_("Developer Options (Advanced)"))
        settings_grid.attach(developer_options, 0, 3, 1, 1)

        self.developer_grid = Gtk.VBox()
        self.developer_grid.set_margin_left(12)
        self.developer_grid.set_margin_top(12)
        self.developer_grid.set_margin_right(12)
        self.developer_grid.set_margin_bottom(12)
        self.developer_grid.set_spacing(12)
        developer_options.add(self.developer_grid)

        developer_label = Gtk.Label(_("These options are primarily of interest to developers."))
        developer_label.set_line_wrap(True)
        developer_label.set_halign(Gtk.Align.START)
        developer_label.set_margin_start(5)
        self.developer_grid.add(developer_label)
        self.developer_grid.add(self.source_check)
        self.developer_grid.add(self.proposed_check)

        self.init_distro()
        self.show_distro()

    def block_handlers(self):
        for widget in self.handlers:
            if widget.handler_is_connected(self.handlers[widget]):
                widget.handler_block(self.handlers[widget])

    def unblock_handlers(self):
        for widget in self.handlers:
            if widget.handler_is_connected(self.handlers[widget]):
                widget.handler_unblock(self.handlers[widget])

    def init_distro(self):

        self.handlers[self.source_check] = \
                              self.source_check.connect("toggled",
                                                                   self.on_source_check_toggled)

        for checkbutton in self.checks_grid.get_children():
            self.checks_grid.remove(checkbutton)

        distro_comps = self.ppa.get_distro_sources()

        for comp in distro_comps:
            description = comp.description
            if description == 'Non-free drivers':
                description = _("Proprietary Drivers for Devices")
            elif description == 'Restricted software':
                description = _("Software with Copyright or Legal Restrictions")
            else:
                description = description + " software"

            label = "%s (%s)" % (description, comp.name)
            checkbox = Gtk.CheckButton(label=label)

            checkbox.comp = comp
            self.handlers[checkbox] = checkbox.connect("toggled",
                                                       self.on_component_toggled,
                                                       comp.name)

            self.checks_grid.add(checkbox)
            checkbox.show()

        child_repos = self.ppa.get_distro_child_repos()
        for template in child_repos:
            if template.type == "deb-src":
                continue

            if "proposed" in template.name:
                self.proposed_check.set_label("%s (%s)" % (template.description,
                                                           template.name))
                self.proposed_check.template = template
                self.handlers[self.proposed_check] = self.proposed_check.connect("toggled",
                                                   self.on_proposed_check_toggled,
                                                   template)

        return 0

    def show_distro(self):
        self.block_handlers()

        for checkbox in self.checks_grid.get_children():
            (active, inconsistent) = self.ppa.get_comp_download_state(checkbox.comp)
            checkbox.set_active(active)
            checkbox.set_inconsistent(inconsistent)

        (src_active, src_inconsistent) = self.ppa.get_source_code_enabled()
        self.source_check.set_active(src_active)
        self.source_check.set_inconsistent(src_inconsistent)

        (prop_active, prop_inconsistent) = self.ppa.get_child_download_state(self.proposed_check.template)
        self.proposed_check.set_active(prop_active)
        self.proposed_check.set_inconsistent(prop_inconsistent)

        self.unblock_handlers()
        return 0

    def on_component_toggled(self, checkbutton, comp):
        enabled = checkbutton.get_active()
        try:
            self.ppa.set_comp_enabled(comp, enabled)
        except dbus.exceptions.DBusException:
            self.show_distro()
        return 0

    def on_source_check_toggled(self, checkbutton):
        enabled = checkbutton.get_active()
        try:
            self.ppa.set_source_code_enabled(enabled)
        except dbus.exceptions.DBusException:
            self.show_distro()
        return 0

    def on_proposed_check_toggled(self, checkbutton, comp):
        enabled = checkbutton.get_active()
        try:
            self.ppa.set_child_enabled(comp.name, enabled)
        except dbus.exceptions.DBusException:
            self.show_distro()
        return 0
    
