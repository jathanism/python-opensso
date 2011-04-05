#!/usr/bin/env python

# $Revision $

from distutils.core import setup, Command
import glob
import os
import sys
import unittest

# Get version from pkg index
from opensso import __version__

class CleanCommand(Command):
    description = "cleans up non-package files. (dist, build, etc.)"
    user_options = []
    def initialize_options(self):
        self.files = None
    def finalize_options(self):
        self.files = './build ./dist ./MANIFEST ./*.pyc examples/*.pyc ./*.egg-info'
    def run(self):
        print 'Cleaning: %s' % self.files
        os.system('rm -rf ' + self.files)

long_desc="""
Python interface for OpenSSO/OpenAM.
"""

setup(
    name='python-opensso',
    version=__version__,
    author='Jathan McCollum',
    author_email='jathan+github@gmail.com',
    license='MIT',
    py_modules=['opensso'],
    url='https://github.com/jathanism/python-opensso/',
    description='Python OpenSSO/OpenAM interface',
    long_description=long_desc,
    scripts=[],
    cmdclass = {
        'clean': CleanCommand,
    }
)
