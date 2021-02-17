#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Executable for PyInstaller
$ python pyinstaller launcher.specs
"""

import multiprocessing
import pyr8s.qt

if __name__ == '__main__':
    multiprocessing.freeze_support()
    pyr8s.qt.main.show()
