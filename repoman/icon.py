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
        self.remote_data = flatpak.remotes.remotes[option][remote_name]
        self.remote_name = remote_name
        self.url = self.remote_data['icon']
        self.cached = f'/usr/share/repoman/icon-cache/{self.remote_name}.svg'
        # icon_cache = pathlib.Path('/usr/share/repoman/icon-cache/')
        # icon_cache.mkdir(parents=True, exist_ok=True)
    
    def get_cached(self):
        
        stream = Gio.MemoryInputStream.new_from_bytes(
            GLib.Bytes.new(self.cached)
        )

        pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_margin_top(12)
        image.set_margin_bottom(12)

        return image
    
    def get_icon(self):
        if self.url:
            with urllib.request.urlopen(self.url) as icon:
                svgdata = icon.read()
            
            stream = Gio.MemoryInputStream.new_from_bytes(
                GLib.Bytes.new(svgdata)
            )
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream_at_scale(
                stream,
                64,
                -1,
                True,
                None
            )
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            image.set_margin_top(12)
            image.set_margin_bottom(12)
        
        else:
            image = Gtk.Image.new_from_icon_name(
                'notfound',
                Gtk.IconSize.SMALL_TOOLBAR
            )
            image.props.opacity = 0

        return image
