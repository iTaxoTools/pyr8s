#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parse the nexus file given through the console.
"""

import sys
from . import parse

def main():
    if len(sys.argv) == 2:
        print(' ')
        a = parse.parse(sys.argv[1])
    else:
        print('Usage: python run.py NEXUS_FILE')
        print('Ex:    python run.py tests/legacy_1')
