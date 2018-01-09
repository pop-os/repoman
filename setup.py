#!/usr/bin/python3

from distutils.core import setup

setup(
    name='Repoman',
    version='0.0.6',
    author='Ian Santopietro',
    description='Easily manage PPAs',
    url='https://github.com/pop_os/repoman',
    license='GNU GPL3',
    scripts=['repoman'],
    packages=['repoman'],
    data_files=[
        ('share/metainfo', ['data/repoman.appdata.xml']),
        ('share/applications', ['data/repoman.desktop']),
        ('share/repoman', ['data/style.css']),
        ('lib/repoman', ['repoman.pkexec']),
    ],
)
