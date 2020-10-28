#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parameter defaults for use by core.Analysis class.
To be extended with helpstrings and ranges.
"""

class Param:

    def __init__(self):

        # Method and Algorithm to use
        self.algorithm = 'nprs'
        self.method = 'powell'

        # General options
        self.general = {
            'perturb_factor': 0.01,
            'scalar': False, #! not used right now, should force root age at 1.0
            'number_of_guesses': 10, # How many times to solve the problem
            'largeval': 1e30, # For clamping
            }
        # Branch length formatting
        self.branch_length = {
            'persite': False,
            'nsites': 1,
            'round': False,
            }
        # Define the behaviour of manual barrier penalty
        self.barrier = {
            'manual': True,
            'max_iterations': 10,
            'initial_factor':0.25,
            'multiplier': 0.10,
            'tolerance': 0.0001,
            }
        self.nprs = {
            'logarithmic': False,
            'exponent': 2,
            }
