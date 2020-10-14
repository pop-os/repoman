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
import subprocess
import threading
from urllib.parse import urlparse

import dbus
import gi
from gi.repository import GLib
import repolib


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
    repo = repolib.SystemSource()
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

    if get_system:
        try:
            system = get_repo_for_name('system')
            sources['system'] = system
        except Exception:
            pass
    sources_dir = repolib.util.get_sources_dir()
    sources_files = sources_dir.glob('*.sources')
    list_files = sources_dir.glob('*.list')
    try:
        sources_list_file = sources_dir.parent / 'sources.list'
    except FileNotFoundError:
        sources_list_file = None
    
    log.debug('Loading .sources files')
    for file in sources_files:
        if file.name == 'system.sources':
            # We loaded system before (or didn't because we aren't supposed to)
            continue
        log.debug('Loading %s', file)
        source = repolib.Source(filename=file.name)
        source.load_from_file()
        sources[source.filename] = source
    
    log.debug('Loading .list files')
    for file in list_files:
        log.debug('Loading %s', file)
        source = repolib.LegacyDebSource(filename=file.name)
        source.load_from_file()
        sources[source.filename] = source
    
    if sources_list_file:
        sources['sources.list'] = {}
    
    return sources

def get_os_codename():
    """ Returns the current OS codename."""
    return repolib.util.DISTRO_CODENAME

def validate(line):
    """ Validate a repo line. """
    return repolib.util.validate_debline(line)

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

def _do_add_source(name, line, dialog):
    new_source = repolib.LegacyDebSource()
    if line.startswith('ppa:'):
        bin_repo = repolib.PPALine(line)
    elif line.startswith('deb'):
        bin_repo = repolib.DebLine(line)
    
    src_repo = bin_repo.copy()
    src_repo.enabled = False

    new_source.name = bin_repo.name
    new_source.sources.append(bin_repo)
    new_source.sources.append(src_repo)
    new_source.load_from_sources()
    new_source.make_names()
    log.debug('New source: %s', new_source.make_deblines())
    new_source.save_to_disk()
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
    bus = dbus.SystemBus()
    privileged_object = bus.get_object('org.pop_os.repolib', '/Repo')
    privileged_object.delete_source(repo)
    privileged_object.exit()
