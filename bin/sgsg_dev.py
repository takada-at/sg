#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function)

import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from sg.commands import group


def main():
    group(obj={})


if __name__ == '__main__':
    main()
