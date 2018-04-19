#!/usr/bin/python3

from distutils.core import setup

setup(
    name='Repoman',
    version='1.0.0',
    author='Ian Santopietro',
    description='Easily manage PPAs',
    url='https://github.com/isantop/repoman',
    license='GNU GPL3',
    scripts=['repoman/repoman'],
    packages=['repoman'],
    data_files=[
        ('share/metainfo', ['data/repoman.appdata.xml']),
        ('share/polkit-1/actions', ['data/org.pop.pkexec.repoman.policy']),
        ('share/repoman', ['data/style.css']),
        ('share/repoman/po/es/LC_MESSAGES', ['po/es/repoman.mo']),
        ('share/repoman/po/sv/LC_MESSAGES', ['po/sv/repoman.mo']),
        ('lib/repoman', ['repoman.pkexec']),
    ],
)
