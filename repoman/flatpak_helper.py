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
from os.path import join
from pathlib import Path
from threading import Thread

gi.require_version('Flatpak', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GObject, Gio, Flatpak, GLib, GdkPixbuf, Gtk

log = logging.getLogger('repoman.flatpak-helper')

# Get User Installation
fp_user_path = join(Path.home(), '.local', 'share', 'flatpak')
fp_user_file = Gio.File.new_for_path(fp_user_path)
fp_user_inst = Flatpak.Installation.new_for_path(fp_user_file, True, None)

# Get System Installation
fp_sys_path = join('/var', 'lib', 'flatpak')
fp_sys_file = Gio.File.new_for_path(fp_sys_path)
fp_sys_inst = Flatpak.Installation.new_for_path(fp_sys_file, False, None)

# Functions
def add_remote(widget, name, url, option):
    """ Adds a remote to the user installation.

    We do user installations by default because that's all that Pop Shop 
    operates on currently. There are maybe plans to allow system-wide remotes, 
    but these aren't yet finalized.

    Arguments:
        name (str): The internal name for the new remote.
        file (Gio.Bytes): The data for the flatpakrepo file to add.
    """
    log.info('Adding remote: %s', name)
    add_thread = AddThread(widget, name, url, option)
    add_thread.start()

def delete_remote(widget, name, option):
    """ Deletes a remote from the installation of option.

    Arguments:
        widget (Gtk.Widget): A widget to manipulate once the thread is finished.
        name (str): The name of the remote to remove.
        option (str): The installation which the remote is configured on.
    """
    log.info('Removing remote: %s', name)
    remove_thread = RemoveThread(widget, name, option)
    remove_thread.start()

def get_icon_cache_for_remote(name, option):
    """ Gets the path to the cached icon for a remote.

    Arguments:
        name (str): The name of the remote to get the icon for.
        option (str): Which installation the remote is on.
    
    Returns:
        `Pathlib.Path` for the required path.
    """
    installation = get_installation_for_type(option)
    remote = installation.get_remote_by_name(name)
    installation_dir = installation.get_path().get_path()
    cache_dir = Path(join(installation_dir, 'repo', 'icon_cache'))
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_icon = Path(join(cache_dir, f'{remote.get_name()}.svg'))
    return cache_icon

def get_installation_for_type(option):
    """ Gets the installation for the given type.

    Arguments:
        option (str): The type to get, 'user' or 'system'
    
    Returns:
        The requested :obj:`Flatpak.Installation`
    """
    log.debug('Getting %s Installation', option)

    # We want to drop the caches for these installations in case they have been
    # modified from some other source.
    if option.lower() == 'user':
        log.debug('User installation found.')
        fp_user_inst.drop_caches()
        return fp_user_inst
    else:
        log.debug('System installation found.')
        fp_sys_inst.drop_caches()
        return fp_sys_inst

def get_installed_refs_from_remote(name, option):
    """Get a list of refs installed from a remote.

    Arguments:
        name (str): The name of the remote to look on
        option (str): Whether this is a `user` or `system` remote.
    
    Returns:
        [`Flatpak.Remote`] The list of remotes.
    """
    installation = get_installation_for_type(option)
    refs = []

    for ref in installation.list_installed_refs_by_kind(Flatpak.RefKind.APP):
        if ref.get_origin() == name:
            refs.append(ref)

    for ref in installation.list_installed_refs_by_kind(Flatpak.RefKind.RUNTIME):
        if ref.get_origin() == name:
            refs.append(ref)
    
    return refs

def get_remotes(option):
    """ Get a list of remotes.

    Arguments:
        option (str): The type of remotes to get, 'user' or 'system'.
    
    Returns:
        A `list` of :obj:`Flatpak.Remote` objects.
    """
    log.debug('Fetching %s remotes', option)
    installation = get_installation_for_type(option)
    return installation.list_remotes()

def get_image_from_pixbuf(pixbuf):
    """Gets an image from the given pixbuf.

    Arguments:
        pixbuf (`GdkPixbuf.Pixbuf`): The pixbuf to get an image.
    
    Returns:
        A `Gtk.Image` with the contents of the pixbuf.
    """
    image = Gtk.Image.new_from_pixbuf(pixbuf)
    image.set_margin_top(12)
    image.set_margin_bottom(12)
    return image

def get_icon_pixbuf(path):
    """ Gets a pixbuf of an image from a given path.

    Arguments:
        path (`Pathlib.Path`): The path item of the image to get.
    
    Returns:
        A `GdkPixbuf.Pixbuf` of the image at `path`.
    """
    try: 
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            str(path), 64, -1, True
        )
        log.debug('Cached icon found')
        return pixbuf
    except GLib.GError:
        log.debug('No cached icon found!')
        return None

def get_installed_refs_for_option(option):
    """ Lists all refs installed on the installation for option.

    Arguments:
        option (str): The installation to list, 'user' or 'system.
    
    Returns:
        A `list` of `Flatpak.Remotes` installed on the specified installation.
    """
    log.debug('Getting refs installed on %s', option)
    installation = get_installation_for_type(option)
    return installation.list_installed_refs()

def strip_bold_from_name(name):
    name = name.replace('<b>', '')
    name = name.replace('</b>', '')
    return name

def validate_flatpakrepo(url):
    """ Validate that url looks like a valid flatpakrepo file.

    Arguments:
        url (str): The URL pointing at the flatpakrepo file.
    
    Returns:
        `True` if the URL looks to be valid.
    """
    url_list = url.split('.')
    log.debug("Validating: %s", url)

    if url_list[-1] == 'flatpakrepo':
        return True
    
    else:
        return False

# Classes
class RemoveThread(Thread):

    def __init__(self, parent, remote, option):
        super().__init__()
        self.option = option
        self.parent = parent
        self.remote = remote
        self.refs = list(self.populate_refs_on_remote(option))
        self.log = logging.getLogger(f'repoman.remove-{remote}')

    def populate_refs_on_remote(self, option):
        for ref in get_installed_refs_for_option(option):
            if ref.get_origin() == self.remote:
                yield ref
    
    def run(self):
        installation = get_installation_for_type(self.option)
        for ref in self.populate_refs_on_remote(self.option):
            self.log.warning(
                'Removing ref %s (%s)', ref.get_name(), ref.get_appdata_name()
            )
            installation.uninstall(
                ref.get_kind(),
                ref.get_name(),
                None,
                ref.get_branch()
            )
        installation.remove_remote(self.remote)
        GObject.idle_add(self.parent.parent.parent.stack.flatpak.generate_entries)
        GObject.idle_add(self.parent.parent.parent.stack.flatpak.view.set_sensitive, True)
        GObject.idle_add(self.parent.parent.parent.hbar.spinner.stop)

class AddThread(Thread):

    def __init__(self, parent, name, url, option):
        super().__init__()
        self.parent = parent
        self.name = name
        self.url = url
        self.option = option

    def run(self):
        installation = get_installation_for_type(self.option)
        repofile = Gio.File.new_for_uri(self.url)
        try:
            log.debug('Loading file from %s', self.url)
            a, contents, b = repofile.load_contents()
            log.debug('File loaded')
            repodata = GLib.Bytes.new(contents)
            
            log.debug('Creating Remote Object for %s', self.name)
            new_remote = Flatpak.Remote.new_from_file(self.name, repodata)
            log.debug('Adding remote %s to %s', new_remote.get_name(), self.option)
            installation.add_remote(new_remote, True, None)
        
        except GLib.Error as e:
            log.warning('Could not add flatpakrepo %s (%s)', self.url, e.args)
            self.throw_error(e.args[0])
            contents = None
        
        GObject.idle_add(self.parent.parent.parent.stack.flatpak.generate_entries)
        GObject.idle_add(self.parent.parent.parent.stack.flatpak.view.set_sensitive, True)
        GObject.idle_add(self.parent.parent.parent.hbar.spinner.stop)
    
    def throw_error(self, message):
            GObject.idle_add(
                self.parent.parent.parent.stack.flatpak.throw_error_dialog,
                message, 
                "error"
            )

class IconThread(Thread):

    def __init__(self, dialog, name, option):
        super().__init__()
        self.dialog = dialog
        self.name = name
        self.option = option
        self.log = logging.getLogger(f'repoman.{self.name}-icon')

    def run(self):
        installation = get_installation_for_type(self.option)
        remote = installation.get_remote_by_name(self.name)
        icon_url = remote.get_icon()

        if not icon_url:
            # No icon to fetch
            self.log.debug('No icon for %s', self.name)
            return
        
        self.log.debug('Getting icon for %s', self.name)
        cache_icon = get_icon_cache_for_remote(self.name, self.option)

        try:
            _icon = Gio.File.new_for_uri(icon_url)
            a, contents, b = _icon.load_contents()
            with open(cache_icon, mode='w') as cache:
                cache.write(contents.decode('UTF-8'))
        
        except GLib.Error as e:
            self.log.warning('Could not load latest icon: %s', e.args)

        pixbuf = get_icon_pixbuf(cache_icon)
        
        if pixbuf:
            image = get_image_from_pixbuf(pixbuf)
        
        else:
            image = Gtk.Image.new_from_icon_name(
                'notfound',
                Gtk.IconSize.SMALL_TOOLBAR
            )
            image.props.opacity = 0
    
        if self.dialog:
            GLib.idle_add(self.dialog.set_remote_icon, image)
