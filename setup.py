#!/usr/bin/env python
"""
installer for Ren'Py Visual Runtime Editor

the old versions of pip installed packages are required for python2.7 support,
which Ren'py uses.
"""

from setuptools import setup, find_packages
from setuptools.command.install import install as InstallCommand
from pip import main as pip_main


class Install(InstallCommand):
    """ Customized setuptools install command which uses pip. """

    def run(self, *args, **kwargs):
        pip_main(['install', '.'])
        InstallCommand.run(self, *args, **kwargs)


setup(
    name='RVRE',
    version='1.0',
    description='Ren\'Py Visual Runtime Editor',
    author='Arjay Ceekay',
    author_email='Ar.JayCee.Kay@gmail.com',
    cmdclass={
        'install': Install,
    },
    packages=find_packages(),
    install_requires=[
        'pyperclip',
        'pyspellchecker==0.5.6',
        'pygments==2.5.2',
        'gitpython==2.1.11'
    ]
)
