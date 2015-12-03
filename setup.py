#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

import ast
from setuptools import setup, find_packages
import os
import re


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('sg/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


def readfile(fpath):
    base = os.path.dirname(__file__)
    fullpath = os.path.join(base, fpath)
    with open(fullpath, 'rb') as fio:
        data = fio.read().decode('utf-8')

    return data


setup(name='sg',
      version=version,
      description='',
      long_description=readfile('README.md'),
      scripts=['bin/sgsg.py'],
      author='takada-at',
      author_email='takada-at@klab.com',
      packages=find_packages('.'),
      install_requires=readfile('requirements.txt').split('\n'),
      tests_require=readfile('requirements-dev.txt').split('\n'),
      )
