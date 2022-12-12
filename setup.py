#!/usr/bin/python3

from distutils.core import setup
from distutils.command.install import install
from distutils.core import Command
import sys, os

podir = "po"
pos = [x for x in os.listdir(podir) if x[-3:] == ".po"]
langs = sorted([os.path.split(x)[-1][:-3] for x in pos])

def modir(lang):
    mobase = "po"
    return os.path.join(mobase, lang)

def polist():
    dst_tmpl = "/usr/share/locale/%s/LC_MESSAGES/"
    polist = [(dst_tmpl % x, ["%s/%s.mo" % (modir(x), 'repoman')]) for x in langs]

    return polist

setup(
    name = 'repoman',
    version = '1.4.0',
    description = 'Easily manage software sources',
    url = 'https://github.com/pop-os/repoman',
    license = 'GNU GPL3',
    packages=['repoman'],
    data_files = [
        ('/usr/share/metainfo', ['data/repoman.appdata.xml']),
        ('/usr/share/applications', ['data/repoman.desktop', 'data/flatpak-installer.desktop']),
        ('/usr/share/repoman', ['data/style.css']),
        ('/usr/lib/repoman', ['data/repoman.pkexec'])
    ] + polist(),
    scripts = ['repoman/repoman', 'repoman/flatpak-installer'],
)
