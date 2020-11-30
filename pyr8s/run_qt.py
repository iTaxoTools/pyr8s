#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Display the graphical interface.
"""

import sys
from . import qt

def main():
    if len(sys.argv) <= 2:
        a = qt.main.show(sys)
    else:
        print('Usage: pyr8s_qt NEXUS_FILE')
        print('Ex:    pyr8s_qt tests/legacy_1')
