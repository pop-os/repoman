#!/usr/bin/python3

from distutils.core import setup

setup(
    name='Repoman',
    version='0.0.6',
    author='Ian Santopietro',
    description='Easily manage PPAs',
    url='https://github.com/isantop/repoman',
    license='GNU GPL3',
    scripts=['repoman/repoman'],
    packages=['repoman'],
    data_files=[
        ('share/metainfo', ['data/repoman.appdata.xml']),
        ('share/applications', ['data/repoman.desktop']),
        ('share/repoman', ['data/style.css']),
        ('share/repoman/po/es/LC_MESSAGES', ['po/es/repoman.mo']),
        ('share/repoman/po/sv/LC_MESSAGES', ['po/sv/repoman.mo']),
        ('lib/repoman', ['repoman.pkexec']),
    ],
)
