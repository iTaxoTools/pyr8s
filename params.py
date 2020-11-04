#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parameter defaults for use by core.Analysis class.
To be extended with helpstrings and ranges for each variable.
"""

class Param:

    def __init__(self):

        # Method and Algorithm to use
        self.algorithm = 'powell'
        self.method = 'nprs'

        # General options
        self.general = {
            'perturb_factor': 0.01,
            'scalar': False, # force root age at 1.0
            'number_of_guesses': 2, #! 10 how many times to solve the problem
            'largeval': 1e30, # For clamping
            }
        # Branch length formatting
        self.branch_length = {
            'persite': False,
            'round': True, # Always true or algorithms don't diverge somehow...
            }
        # Define the behaviour of manual barrier penalty
        self.barrier = {
            'manual': True, # True
            'max_iterations': 10, #! 10
            'initial_factor': 0.25,
            'multiplier': 0.10,
            'tolerance': 0.0001,
            }
        self.nprs = {
            'logarithmic': False, #! NOT USED
            'exponent': 2, #! NOT USED
            }
        self.powell = {
            'variable_tolerance': 1e-8,
            'function_tolerance': 1e-8,
            }
