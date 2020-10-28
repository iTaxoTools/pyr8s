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
            'persite': False, # These affect effective branch lengths
            'nsites': 1, # These affect effective branch lengths
            'round': False, # These affect effective branch lengths
            'perturb_factor': 0.01,
            'scalar': False, #! not used right now, should force root age at 1.0
            'number_of_guesses': 10, # How many times to solve the problem
            'largeval': 1e30, # For clamping
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
