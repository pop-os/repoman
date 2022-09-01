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

import logging
from pathlib import Path
import subprocess
import threading
import traceback
from urllib.parse import urlparse

import dbus
import gi
from gi.repository import GLib, Gtk
import repolib

repolib.set_logging_level(2)

repolib.system.load_all_sources()
sources = repolib.util.sources
errors = repolib.util.errors
load_all_sources = repolib.system.load_all_sources

log = logging.getLogger("repoman.Repo")
log.debug('Logging established')

def _do_edit_system_legacy_sources_list(name):
    try:
        subprocess.run(['gedit', 'admin:///etc/apt/sources.list'])
    except FileNotFoundError:
        try:
            subprocess.run([
                'gnome-terminal', 
                '--', 
                'sudo', 'editor', '/etc/apt/sources.list'
            ])
        except FileNotFoundError:
            subprocess.run([
                'x-terminal-emulator',
                '-e', 
                'sudo',
                'editor',
                '/etc/apt/sources.list'
            ])

def edit_system_legacy_sources_list():
    thread = threading.Thread(
        target=_do_edit_system_legacy_sources_list,
        args=(1,)
    )
    thread.start()

def get_system_repo():
    """Get a repo for the system sources. """
    repo = repolib.util.sources['system']
    return repo

def url_validator(url):
    """ Validate a url and tell if it's good or not.

    FIXME: We should use the validator provided by Repolib. Change this once 
    that one is merged.

    Arguments:
        url (str): The URL to validate.

    Returns:
        `True` if `url` is not malformed, otherwise `False`.
    """
    try:
        # pylint: disable=no-else-return,bare-except
        # A) We want to return false if the URL doesn't contain those parts
        # B) We need this to not throw any exceptions, regardless what they are
        result = urlparse(url)
        if result.netloc:
            # We need at least a scheme and a netlocation/hostname or...
            return all([result.scheme, result.netloc])
        elif result.path:
            # ...a scheme and a path (this allows file:/// URIs which are valid)
            return all([result.scheme, result.path])
        return False
    except:
        return False

def get_repo_for_name(name):
    """ Get a repo from a given name.

    This takes a name and gives back a repolib.Source object which represents 
    the given source.

    Arguments:
        name (str): The name of the repo to look for.
    
    Returns:
        A repolib.Source (or subclass) representing the given name.
    """
    full_path = repolib.util.get_source_path(name)
    if full_path:
        if full_path.suffix == '.sources':
            repo = repolib.Source(filename=full_path)
        else:
            repo = repolib.LegacyDebSource(filename=full_path)
        
        return repo
    raise Exception(f'Could not find a source for {name}.')

def get_all_sources(get_system=False):
    """ Returns a dict with all sources on the system.
    
    The keys for each entry in the dict are the names of the sources.
    The values are the corresponding repolin.Source subclass

    Arguments:
        get_system (bool): whether to include the system sources or not.
    
    Returns:
        The above described dict.
    """
    sources = {}
    sources_dir = Path(repolib.SOURCES_DIR)
    try:
        sources_list_file = sources_dir.parent / 'sources.list'
    except FileNotFoundError:
        sources_list_file = None
    
    sources_list = repolib.util.sources
    errors = repolib.util.errors

    for source in sources_list:
        sources[source] = sources_list[source]
    
    if sources_list_file:
        sources['sources.list'] = {}
    
    return sources, errors

def get_os_codename():
    """ Returns the current OS codename."""
    return repolib.util.DISTRO_CODENAME

def validate(line):
    """ Validate a repo line. """
    if line.startswith('deb'):
        return repolib.util.validate_debline(line)
    elif line.startswith('ppa'):
        linel = line.split(':')
        if not len(linel) > 1:
            return False
        if not '/' in linel[-1]:
            return False
        return True
    elif line.startswith('popdev'):
        if not ':' in line:
            return False
        return True

def get_os_name():
    """ Returns the current OS name, or fallback if not available."""
    try:
        with open("/etc/os-release") as os_release_file:
            os_release = os_release_file.readlines()
            for line in os_release:
                parse = line.split('=')
                if parse[0] == "NAME":
                    if parse[1].startswith('"'):
                        return parse[1][1:-2]
                    else:
                        return parse[1][:-1]
                else:
                    continue
    except FileNotFoundError:
        return "your OS"

    return "your OS"

def get_error_messagedialog(parent, text, exc, prefix):
    """ Get an error dialog to display an error to the user.

    Arguments:
        parent (:obj:`Gtk.Window`): The transient parent for the dialog
        text (str): The main/title text of the dialog.
        exc (:obj:`Exception`): The exception which threw the error
        tb (:obj:`traceback`): The traceback of the error
    
    Returns:
        A :obj:`Gtk.MessageDialog`
    """
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        flags=0,
        message_type=Gtk.MessageType.ERROR,
        buttons=Gtk.ButtonsType.CANCEL,
        text=text,
    )

    traceback_text = ' '.join(traceback.format_tb(exc.__traceback__))
    secondary_text = GLib.markup_escape_text(str(exc))
    dialog.format_secondary_markup(f'{prefix}:\n{secondary_text}')
    content_area = dialog.get_content_area()
    
    expander = Gtk.Expander.new('Error details:')
    traceback_label = Gtk.Label.new(traceback_text)
    traceback_label.set_line_wrap(True)
    expander.add(traceback_label)
    content_area.add(expander)

    action_area = dialog.get_action_area()
    action_area.set_layout(Gtk.ButtonBoxStyle.EXPAND)
    dialog.show_all()

    return dialog

def _do_add_source(name, line, dialog):
    try:
        # New process with key management
        disabled = False 
        skip_keys = False
        add_source = None

        # Add the source disabled if it's preceded with a '#'/commented out
        if line.startswith('#'):
            line = line.replace('#', '')
            disabled = True

        if line.startswith('http') and len(line.split()) == 1:
            line = f'deb {line} {repolib.util.DISTRO_CODENAME} main'
        
        for prefix in repolib.shortcut_prefixes:
            if line.startswith(prefix):
                add_source = repolib.shortcut_prefixes[prefix]()
        
        add_source.load_from_data([line])

        # Possibly add source code toggle in the future?

        add_source.enabled = True
        if line.startswith('#'):
            add_source.enabled = False
        
        if not add_source.ident:
            add_source.generate_default_ident()
        
        add_file = repolib.SourceFile(name=add_source.ident)
        add_file.format = add_source.default_format
        add_file.add_source(add_source)
        add_source.file = add_file

        log.debug('File format: %s', add_file.format)
        log.debug('File path: %s', add_file.path)
        log.debug('Sources in file %s:\n%s', add_file.path, add_file.sources)

        add_file.save()

    except Exception as err:
        GLib.idle_add(dialog.show_error, err)
    GLib.idle_add(dialog.destroy)

def add_source(line, dialog):
    """ Add a legacy deb source to the system.

    Arguments:
        line (str): the deb line to add.
    """
    log.debug('Adding repo %s', line)
    dialog.set_busy()
    thread = threading.Thread(target=_do_add_source, args=(1, line, dialog))
    thread.start()

def delete_repo(repo):
    """ Delete a repo from the sytem.

    Note: This is about the only thing we need dbus for, so we use it here
    and only here.
    """
    remove_source = repo.filename
    remove_key = repo.key_file
    bus = dbus.SystemBus()
    privileged_object = bus.get_object('org.pop_os.repolib', '/Repo')
    privileged_object.delete_source(remove_source, remove_key.name)
    privileged_object.exit()
    return True
