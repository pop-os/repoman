#!/usr/bin/python3
'''
   Copyright 2020 Ian Santopietro (ian@system76.com)

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
import os
import pathlib
import urllib

gi.require_versions(
    {
        'Gtk': '3.0',
        'GLib': '2.0',
        'Gio': '2.0'
    }
)
from gi.repository import Gtk, GLib, GdkPixbuf, Gio

import pyflatpak as flatpak

class RemoteIcon:
    def __init__(self, remote_name, option):
        self.log = logging.getLogger('repoman.icon_tool')
        self.cancellable = Gio.Cancellable()
        self.remote_data = flatpak.remotes.remotes[option][remote_name]
        self.remote_name = remote_name
        self.url = self.remote_data['icon']

        self.cache_dir = pathlib.Path(
            os.path.join(
                flatpak.remotes.fp_user_config_filepath,
                'repo',
                'icon_cache'
            )
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cached = os.path.join(self.cache_dir, f'{self.remote_name}.svg')

    
    def get_cached(self):
        """Get a cached icon for the remote.
        
        Usually we get this when we first add the remote, so it should be 
        present on-disk as a fallback.
        """

        self.log.debug('Getting cached icon from %s', self.cached)
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                self.cached, 64, -1, True
            )
            self.log.debug('Cached icon found')
        except GLib.GError:
            self.log.debug('No cached icon found!')
            return self.get_no_icon()

        image = self.get_image_from_pixbuf(pixbuf)
        return image
    
    def get_no_icon(self):
        image = Gtk.Image.new_from_icon_name(
            'notfound',
            Gtk.IconSize.SMALL_TOOLBAR
        )
        image.props.opacity = 0

        return image
    
    def get_image_from_pixbuf(self, pixbuf):

        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_margin_top(12)
        image.set_margin_bottom(12)
        return image
            