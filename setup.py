#!/usr/bin/python3

from distutils.core import setup

setup(
    name='Repoman',
    version='0.0.6',
    author='Ian Santopietro',
    description='Easily manage PPAs',
    url='https://github.com/pop_os/repoman',
    license='GNU GPL3',
    scripts=['org.pop_os.repoman'],
    packages=['repoman'],
    data_files=[
        ('share/metainfo', ['data/org.pop_os.repoman.appdata.xml']),
        ('share/repoman', ['data/style.css']),
        ('lib/repoman', ['org.pop_os.repoman.pkexec']),
    ],
)
