#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parse the nexus file given through the console.
"""

import sys
from .. import parse

if __name__ == '__main__':
    print(' ')
    if len(sys.argv) >=2:
        a = parse(sys.argv[1])
