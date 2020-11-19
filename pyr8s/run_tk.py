#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Display the graphical interface.
"""

import sys
from . import tk

def main():
    if len(sys.argv) > 1:
        print('Warning: Arguments ignored.')
    tk.main.show()
