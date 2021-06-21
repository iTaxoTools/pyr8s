#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Launch the pyr8s GUI"""

import multiprocessing
from itaxotools.pyr8s.gui import run

if __name__ == '__main__':
    multiprocessing.freeze_support()
    run.main()
