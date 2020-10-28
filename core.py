#! /usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
## pyr8s: Divergence Time Estimation
##
## Copyright 2020 Stefanos Patmanidis.
## All rights reserved.
##############################################################################

"""
Extend dendropy trees with utility functions and attributes.
"""

import dendropy
import random

from scipy import optimize
from math import log

import extensions


##############################################################################
### Helper function

def apply_fun_to_list(function, lista):
    """
    Used together with min and max to avoid comparing with None.
    If lista only has Nones, return None.
    """

    # Previous solution also trimmed 0s, which we want to keep
    # clean = list(filter(None, lista))
    # return (function)(clean) if any(clean) else None

    clean = list(i for i in filter(lambda x: x is not None, lista))
    return (function)(clean) if len(clean) else None


##############################################################################
### Analysis

class Analysis:
    """
    All the work happens here
    """
    #? Consider locking attributes with __slots__ or @dataclass

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

    class Array:
        pass

    def __init__(self):

        random.seed()

        self.param = self.Param()
        self.array = None
        self.tree = None

        #! Somehow read tree here, dummy in place
        # Make sure the tree has at least one root and one node

        s = "(A:10,(B:9,(C:8,(D:7,E:6))H):4)V:3;"
        s = "(A:10,(B:9,(C:8,(D:7,:6))H):4):3;"
        # Force internal nodes as taxa, would have been labels otherwise
        t = dendropy.Tree.get_from_string(s, "newick", suppress_internal_node_taxa=False)
        t.is_rooted = True
        t.collapse()
        t.index()
        t.order()
        t.seed_node.max = 510
        t.seed_node.min = 490
        t.nodes()[2].min = 90
        t.nodes()[2].max = 400
        t.nodes()[5].fix = 200
        self.tree = t




    def _array_solution_merge(self):
        """Merge fixed ages and variables into array.solution"""

        array = self.array

        array.solution = []
        for i in range(0,array.n):
            if array.age[i] is not None:
                array.solution.append(array.age[i])
            else:
                array.solution.append(array.variable[array.unmap[i]])


##############################################################################
### Function generators

    def _build_barrier_penalty(self):
        """Generate penalty function"""

        largeval = self.param.general['largeval']
        array = self.array

        def barrier_penalty(x):
            """
            Keep variables away from bounds
            """

            def barrier_term(x):
                if x > 0:
                    return 1/x
                else:
                    return largeval

            sum = 0
            for i in array.map:
                j = array.unmap[i]
                if array.high[i] is not None:
                    sum += barrier_term(array.high[i] - array.variable[j])
                if array.low[i] is not None:
                    sum += barrier_term(array.variable[j] - array.low[i])
            # print('Barrier penalty: {0}'.format(sum))
            return sum

        return barrier_penalty


    def _build_objective_nprs(self):
        """Generate the objective function"""

        logarithmic = self.param.nprs['logarithmic'] #bool
        exponent = self.param.nprs['exponent'] #2
        largeval = self.param.general['largeval']
        array = self.array

        def local_rate(i):
            parent = array.parent[i]
            dt = array.solution[parent] - array.solution[i]
            if dt <= 0:
                print('Parent younger than child while calculating rate! {0} < {1}'.
                    format(array.solution[parent], array.solution[i]))
                return largeval
            dx = array.length[i]
            rate = dx/dt
            if logarithmic:
                rate = log(rate)
            return rate

        def objective_nprs(x):
            """
            Ref Sanderson, Minimize neighbouring rates
            """
            # print('Objective: x = {0}'.format(x))

            array.variable = x
            self._array_solution_merge()

            # Calculate all rates first
            for i in range(1,array.n):
                array.rate[i] = local_rate(i)

            # Sum of terms that don't involve root
            wk = 0
            # Sums and count of terms that involve root
            sr, srr, n0 = 0, 0, 0
            # Ignore root
            for i in range(1,array.n):
                parent = array.parent[i]
                if parent == 0:
                    n0 += 1
                    sr += array.rate[i]
                    srr += array.rate[i] ** 2
                else:
                    wk += abs(array.rate[parent] - array.rate[i]) ** exponent
            w0 = (srr - (sr*sr)/n0) / n0
            # print('Objective: {0}'.format(w0 + wk))
            return w0 + wk


        return objective_nprs


    def print(self):
        """Quick method to print the tree"""
        self.tree.print_plot(show_internal_node_labels=True)

    def array_make(self):
        """
        Convert the tree into arrays, preparing them for analysis.
        The nodes are listed in preorder sequence.
        """

        # Demand that tree.index() and tree.order() were previously called
        if not self.tree._indexed: raise RuntimeError(
            'You must prepare tree with Tree.index() before calling array_make().')
        if not self.tree._ordered: raise RuntimeError(
            'You must prepare tree with Tree.order() before calling array_make().')

        # Work locally, return result to class array when done.
        array = self.Array()

        array.node = []
        array.label = []
        array.order = []
        for node in self.tree.preorder_node_iter():
            array.node.append(node)
            array.label.append(node.label)
            array.order.append(node.order)
        array.n = len(array.node)

        # This will be used by the optimization function
        array.parent = [0]
        for node in self.tree.preorder_node_iter_noroot():
            array.parent.append(node.parent_node.index)

        array.length = []
        for node in self.tree.preorder_node_iter():
            length = node.edge_length
            if length <= 0:
                raise ValueError('Non-positive length for node {0}'.
                    format(node.label))
            if self.param.general['persite'] == True:
                length *= self.param.general['nsites']
            if self.param.general['round'] == True:
                length = round(length)
            array.length.append(length)

        # Get fixed ages, leaves are fixed to 0 if no constraints are given
        array.age = []
        for node in self.tree.preorder_node_iter():
            fix = node.fix
            if node.is_leaf() and not any([node.fix, node.min, node.max]): fix = 0
            array.age.append(fix)

        # Calculate high boundary for each node (top down).
        high = apply_fun_to_list(min,
            [self.tree.seed_node.max, self.tree.seed_node.fix])
        array.high = [high]
        for node in self.tree.preorder_node_iter_noroot():
            high = apply_fun_to_list(min,
                [node.max, node.fix,
                array.high[node.parent_node.index]])
            array.high.append(high)

        # Calculate low boundary for each node (bottom up).
        # Each node first calculates its own boundary,
        # then it passes it up the tree, so the parent can consider all children.
        #? This can definitely be done by comparing and keeping
        #? the max instead of pushing it up into a list of lists,
        #? but is it really better that way?
        # array.low = [[None] for x in range(array.n)]
        # for node in self.tree.postorder_node_iter_noroot():
        #     low = apply_fun_to_list(max,
        #         [0, node.min, node.fix] + array.low[node.index])
        #     array.low[node.index] = low
        #     array.low[node.parent_node.index].append(low)
        # array.low[0] = apply_fun_to_list(max,
        #     [self.tree.seed_node.min, self.tree.seed_node.fix] + array.low[0])

        array.low = [None] * array.n
        for node in self.tree.postorder_node_iter_noroot():
            low = apply_fun_to_list(max,
                [0, node.min, node.fix, array.low[node.index]])
            array.low[node.index] = low
            parent = node.parent_node.index
            array.low[parent] = apply_fun_to_list(max, [array.low[parent], low])
        array.low[0] = apply_fun_to_list(max,
            [self.tree.seed_node.min, self.tree.seed_node.fix, array.low[0]])

        # Boundary check
        for i in range(array.n):

            # These must be in ascending order:
            # low boundary < fixed age < high boundary
            order = [array.low[i], array.age[i], array.high[i]]
            order = [i for i in filter(lambda x: x is not None, order)]
            if sorted(order) != order:
                raise ValueError('Impossible boundaries for node {0}: {1}]'.
                    format(array.label[i],order))

            # If (existing) boundaries collide, make sure node age is a fixed value
            if all([array.low[i], array.high[i]]):
                if array.high[i] == array.low[i]:
                    array.age[i] = array.high[i]

        # Nodes without value are declared variables for finding
        array.variable = []
        array.map = []
        array.unmap = []
        array.v = 0
        for i, a in enumerate(array.age):
            if a is None:
                array.variable.append(None)
                array.map.append(i)
                array.unmap.append(array.v)
                array.v += 1
            else:
                array.unmap.append(None)

        # Check if the problem even exists
        if array.v < 0:
            raise ValueError('Solution defined by constraints: {0}'.
                format(array.age))

        # Get bounds for variables only
        array.bounds = []
        for j in array.map:
            array.bounds.append((array.low[j],array.high[j]))

        # Keep rates here
        array.rate = [None] * array.n

        # According to original code, either must be true for divergence:
        # - Root has fixed age
        # - An internal node has fixed age
        # - Some node has max age
        # - Tips have different ages
        # I tested the last point and it doesn't seem to hold
        # Equivalent condition: a high boundary exists

        if not any(array.high):
            raise ValueError('Not enough constraints to ensure divergence!')


        #! A range of solutions might exist if root is not fixed!
        #! Might be a good idea to point that out.

        self.array = array

    def guess(self):
        """
        Assign variables between low and high bounds.
        The guess will never touch the boundaries (at least 2% away).
        """

        if self.array is None: raise RuntimeError(
            'You must prepare with array_make() before calling guess().')

        # Reference array here for short.
        array = self.array

        # We will be modifying children high boundaries according to parent guess.
        # Copy array.high to keep these changes temporary
        window = array.high.copy()

        # Gather guesses here:
        variable = []

        # Start with the root if not fixed
        if array.age[0] is None:
            if all((array.low[0], array.high[0])):
                # Both boundaries exist, get a random point within
                high = array.high[0]
                low = array.low[0]
                diff = high - low
                shift = diff * random.uniform(0.02,0.98)
                age = high - shift
            elif array.low[0] is not None:
                #? Static percentages were used in original program...
                age = array.low[0] * 1.25
            elif array.high[0] is not None:
                #? Should we randomise all 3 cases?
                age = array.high[0] * 0.75
            else:
                # This could still diverge as long as there is an internal high boundary.
                # Find that and go higher still.
                age = apply_fun_to_list(max, array.high)
                if age is None: raise RuntimeError(
                    'This will never diverge, should have been caught by make_array()!')
                #? Even this might need to be randomised
                age *= 1.25
            # Window gets narrower for children and root age is saved
            window[0] = age
            variable.append(age)

        # Keep guessing from the top, restricting children as we go.
        for i in range(1,array.n):
            # Child is never older than parent
            window[i] = apply_fun_to_list(min,
                [window[i], window[array.parent[i]]])
            if array.age[i] == None:
                # This node is not fixed, assign a random valid age
                high = window[i]
                low = array.low[i]
                order = array.order[i]
                diff = high - low
                # As per the original code:
                # The term log(order+3) is always greater than 1
                # and gets larger the closer we get to the root.
                # Diving with it makes internal nodes close to root
                # keep away from their lower boundary, thus giving
                # more room for big basal clades to exist.
                shift = diff * random.uniform(0.02,0.98) / log(order+3)
                age = high - shift
                # Window gets narrowed down, age is saved
                window[i] = age
                variable.append(age)

        # Return new guess.
        array.variable = variable

        self._array_solution_merge()

    def perturb(self):
        """
        Shake up the values for a given guess, while maintaining feasibility
        """

        if self.array is None: raise RuntimeError(
            'You must prepare with array_make() before calling perturb().')

        #! Make sure a guess exists in variable
        if not all(self.array.variable):
            raise RuntimeError('There is no complete guess to perturb!')

        # Fetch for ease of use
        array = self.array
        perturb_factor = self.param.general['perturb_factor']

        # Keep lower bound window for each variable
        window = [None] * array.v

        # Start iterating variables only from the bottom up
        # making sure the parent never gets younger than their children
        for j in reversed(range(0,array.v)):

            # j counts variables, i counts everything
            i = array.map[j]
            parent_position = array.parent[i]

            # Determine perturbation window first
            perturb_high = array.variable[j] * (1 + perturb_factor)
            perturb_low = array.variable[j] * (1 - perturb_factor)

            # Catch root, it has no parent so ignore this from upper boundary
            #? Can possibly move this outside
            if array.parent[i] != i:
                parent_age = array.solution[parent_position]
            else:
                parent_age = None

            high = apply_fun_to_list(min,
                [perturb_high, array.high[i], parent_age])

            low = apply_fun_to_list(max,
                [perturb_low, array.low[i], window[j]])

            age = random.uniform(low,high)

            array.variable[j] = age

            # If parent is a variable, adjust its window
            if array.age[parent_position] is None:
                parent_variable = array.unmap[parent_position]
                window_current = window[parent_variable]
                window_new = apply_fun_to_list(max, [age,window_current])
                window[parent_variable] = window_new

        self._array_solution_merge()


    def method_powell(self):
        """
        Repeat method as necessary while relaxing barrier
        """
        objective_nprs = self._build_objective_nprs()

        result = None

        if self.param.barrier['manual'] == True:

            # Adds a barrier_penalty to the objective function
            # to keep solution variables away from their boundaries.
            # We are interested in the pure objective function value.
            # Relax the barrier penalty factor with each iteration,
            # while also perturbing the variables

            barrier_penalty = self._build_barrier_penalty()

            factor = self.param.barrier['initial_factor']
            kept_value = objective_nprs(self.array.variable)

            for b in range(self.param.barrier['max_iterations']):


                print('Barrier iteration: {0}'.format(b))

                result = optimize.minimize(
                    lambda x: objective_nprs(x) + factor*barrier_penalty(x),
                    self.array.variable, method='Powell')

                self.result = result
                self.array.variable = list(result.x)

                new_value = objective_nprs(self.array.variable)

                if new_value == 0:
                    break

                tolerance = abs((new_value - kept_value)/new_value)

                if tolerance < self.param.barrier['tolerance']:
                    break
                else:
                    kept_value = new_value
                    factor *= self.param.barrier['multiplier']
                    self.perturb()

        else:
                result = optimize.minimize(objective_nprs, self.array.variable,
                    method='Powell', bounds=self.array.bounds)

                self.array.variable = list(result.x)

        return result.fun



    def optimize(self):
        """
        Applies the selected algorithm to the given array
        over multiple guesses, keeping the best
        """

        #! This is a good place to output warnings etc
        #! Also to make_array

        kept_min = None

        for g in range(self.param.general['number_of_guesses']):

            self.guess()

            print('Guess {0}: {1}'.format(g, self.array.variable))

            # Call the appropriate optimization method
            if hasattr(self, 'method_' + self.param.method):
                new_min = getattr(self, 'method_' + self.param.method)()
            else:
                raise ValueError('No such method: {0}'.format(self.param.method))

            # merge not needed?? just wanted to print
            self._array_solution_merge()
            print('Local solution: {0}'.format(self.array.solution))

            kept_min = apply_fun_to_list(min, [kept_min, new_min])
            if kept_min == new_min:
                kept_variable = self.array.variable

        self.array.variable = kept_variable
        self._array_solution_merge()
        print('Best solution: {0}'.format(self.array.solution))
        return kept_variable





    def array_take(self):
        """
        Recover tree from arrays after analysis.
        """
        pass

if __name__ == '__main__':
    print('in main')
    a = Analysis()
    a.param.general['persite'] = True
    a.param.general['nsites'] = 100
    a.array_make()

    file = open('../SAMPLE_SIMPLE','r')
    tokenizer = dendropy.dataio.nexusprocessing.NexusTokenizer(file)
    token = tokenizer.next_token_ucase()
    if not token == '#NEXUS':
        raise ValueError('Not nexus file!')

    while not tokenizer.is_eof():
        token = tokenizer.next_token_ucase()
        while token != None and token != 'BEGIN' and not tokenizer.is_eof():
            token = tokenizer.next_token_ucase()
        token = tokenizer.next_token_ucase()
        if token == 'RATES':
            print('RATES FOUND!')
        else:
            while not (token == 'END' or token == 'ENDBLOCK') \
                and not tokenizer.is_eof() \
                and not token==None:
                tokenizer.skip_to_semicolon()
                token = tokenizer.next_token_ucase()


print('Import end.')
