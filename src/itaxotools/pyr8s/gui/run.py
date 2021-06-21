#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Entry point for Qt GUI"""

import sys, os
import multiprocessing
from . import main as qt_main

def main():
    # force spawning on linux for debugging
    # multiprocessing.set_start_method('spawn')
    if len(sys.argv) <= 2:
        a = qt_main.show()
    else:
        basename = os.path.basename(sys.argv[0])
        print('Usage: {} [NEXUS_FILE]'.format(basename))
        print('Ex:    {} examples/legacy_1'.format(basename))
