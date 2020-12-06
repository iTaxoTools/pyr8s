#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Display the graphical interface.
"""

import sys
from . import tk

def main():
    if len(sys.argv) == 1:
        a = tk.main.show()
    elif len(sys.argv) == 2:
        a = tk.main.show(file=sys.argv[1])
    else:
        print('Usage: pyr8s_tk NEXUS_FILE')
        print('Ex:    pyr8s_tk tests/legacy_1')
