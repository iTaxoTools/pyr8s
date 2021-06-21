#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Entry point for console"""

import sys, os
from itaxotools.pyr8s import parse

def main():
    if len(sys.argv) == 2:
        print(' ')
        a = parse.from_file(sys.argv[1], run=True)
    else:
        basename = os.path.basename(sys.argv[0])
        print('Usage: {} NEXUS_FILE'.format(basename))
        print('Ex:    {} examples/legacy_1'.format(basename))
