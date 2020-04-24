#!/usr/bin/python3

from distutils.core import setup
from distutils.command.install import install
from distutils.core import Command
import sys

setup(
    name = 'repoman',
    version = '1.2.2',
    description = 'Easily manage software sources',
    url = 'https://github.com/pop-os/repoman',
    license = 'GNU GPL3',
    packages=['repoman'],
    data_files = [
        ('/usr/share/metainfo', ['data/repoman.appdata.xml']),
        ('/usr/share/dbus-1/system-services', ['data/org.pop_os.repoman.service']),
        ('/usr/share/polkit-1/actions', ['data/org.pop_os.repoman.policy']),
        ('/etc/dbus-1/system.d/', ['data/org.pop_os.repoman.conf']),
        ('/usr/share/applications', ['data/repoman.desktop']),
        ('/usr/share/repoman', ['data/style.css']),
        ('/usr/lib/repoman', ['data/service.py', 'data/repoman.pkexec'])
    ],
    scripts = ['repoman/repoman'],
)
