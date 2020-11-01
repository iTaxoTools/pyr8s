#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Estimate Divergence Times
"""

import dendropy
import random
import numpy as np
import numpy.ma as ma

from scipy import optimize
from math import log

import extensions
import params


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
### Data Arrays

class Array:
    """
    Contains all arrays needed by the optimization methods.
    To be defined using numpy arrays if needed.
    """
    def __init__(self, param):
        # Bind new array options to caller
        self._param = param
        self._tree = None

        self.n = 0
        self.v = 0
        self.node = []
        self.label = []
        self.order = []
        self.parent = []
        self.length = []
        self.subs = []
        self.age = []
        self.high = []
        self.low = []
        self.variable = []
        self.map = []
        self.unmap = []
        self.bounds = []
        self.rate = []


    def solution_merge(self):
        """Merge fixed ages and variables into self.solution"""

        self.solution = []
        for i in range(0,self.n):
            if self.age[i] is not None:
                self.solution.append(self.age[i])
            else:
                self.solution.append(self.variable[self.unmap[i]])

    def make(self, tree):
        """
        Convert the give tree into arrays, preparing them for analysis.
        The nodes are listed in preorder sequence.
        """

        # Keep a copy of given tree to return later
        self._tree = tree.clone(depth=1)
        _tree = self._tree

        scalar = self._param.general['scalar']
        persite = self._param.branch_length['persite']
        nsites = self._param.branch_length['nsites']
        doround = self._param.branch_length['round']

        # Ignore all constraints if scalar
        if scalar:
            for node in _tree.preorder_node_iter():
                node.max = None
                node.min = None
                if node.is_leaf():
                    node.fix = 0
                else:
                    node.fix = None
            _tree.seed_node.fix = 1.0

        # Calculate substitutions and trim afterwards=
        multiplier = nsites if persite == True else None
        _tree.calc_subs(multiplier, doround)
        _tree.collapse()
        _tree.index()
        _tree.order()
        _tree.print_plot()

        # Set branch lengths
        self.length = [None]
        self.subs = [None]
        for node in _tree.preorder_node_iter_noroot():
            self.length.append(node.edge_length)
            self.subs.append(node.subs)

        self.node = []
        self.label = []
        self.order = []
        for node in _tree.preorder_node_iter():
            self.node.append(node)
            self.label.append(node.label)
            self.order.append(node.order)
        self.n = len(self.node)

        # This will be used by the optimization function
        self.parent = [0]
        for node in _tree.preorder_node_iter_noroot():
            self.parent.append(node.parent_node.index)

        # Get fixed ages
        self.age = []
        for node in _tree.preorder_node_iter():
            fix = node.fix
            self.age.append(fix)

        # Get constrained indexes
        self.constrained = []
        for i, node in enumerate(_tree.preorder_node_iter()):
            if node.max is not None or node.min is not None:
                self.constrained.append(i)

        # Calculate high boundary for each node (top down).
        high = apply_fun_to_list(min,
            [_tree.seed_node.max, _tree.seed_node.fix])
        self.high = [high]
        for node in _tree.preorder_node_iter_noroot():
            high = apply_fun_to_list(min,
                [node.max, node.fix,
                self.high[node.parent_node.index]])
            self.high.append(high)

        self.low = [None] * self.n
        for node in _tree.postorder_node_iter_noroot():
            low = apply_fun_to_list(max,
                [0, node.min, node.fix, self.low[node.index]])
            self.low[node.index] = low
            parent = node.parent_node.index
            self.low[parent] = apply_fun_to_list(max, [self.low[parent], low])
        self.low[0] = apply_fun_to_list(max,
            [_tree.seed_node.min, _tree.seed_node.fix, self.low[0]])

        # Boundary check
        for i in range(self.n):

            # These must be in ascending order:
            # low boundary < fixed age < high boundary
            order = [self.low[i], self.age[i], self.high[i]]
            order = [i for i in filter(lambda x: x is not None, order)]
            if sorted(order) != order:
                raise ValueError('Impossible boundaries for node {0}: {1}]'.
                    format(self.label[i],order))

            # If (existing) boundaries collide, make sure node age is a fixed value
            if all([self.low[i], self.high[i]]):
                if self.high[i] == self.low[i]:
                    self.age[i] = self.high[i]

        # Nodes without value are declared variables for finding
        self.variable = []
        self.map = []
        self.unmap = []
        self.v = 0
        for i, a in enumerate(self.age):
            if a is None:
                self.variable.append(None)
                self.map.append(i)
                self.unmap.append(self.v)
                self.v += 1
            else:
                self.unmap.append(None)

        # Check if the problem even exists
        if self.v < 0:
            raise ValueError('Solution defined by constraints: {0}'.
                format(self.age))

        # Get bounds for variables only
        self.bounds = []
        for j in self.map:
            self.bounds.append((self.low[j],self.high[j]))

        # Keep rates here
        self.rate = [None] * self.n

        # According to original code, either must be true for divergence:
        # - Root has fixed age
        # - An internal node has fixed age
        # - Some node has max age
        # - Tips have different ages
        # I tested the last point and it doesn't seem to hold
        # Equivalent condition: a high boundary exists

        if not any(self.high):
            raise ValueError('Not enough constraints to ensure divergence!')

        #! A range of solutions might exist if root is not fixed!
        #! Might be a good idea to point that out.

        # self.node = numpy.array(self.node)
        # self.label = numpy.array(self.label)
        # self.order = numpy.array(self.order)
        # self.parent = numpy.array(self.parent)
        # self.length = numpy.array(self.length)
        # self.subs = numpy.array(self.subs)
        # self.age = numpy.array(self.age)
        # self.high = numpy.array(self.high)
        # self.low = numpy.array(self.low)
        # self.variable = numpy.array(self.variable)
        # self.map = numpy.array(self.map)
        # self.unmap = numpy.array(self.unmap)
        # self.bounds = numpy.array(self.bounds)
        # self.rate = numpy.array(self.rate)

        # self.xvariable = np.array(self.variable, dtype=float)
        # self.xhigh = np.array(self.high, dtype=float)
        # self.xlow = np.array(self.low, dtype=float)
        # mask = [1]*len(self.xhigh)
        # mask[0] = 0
        # self.xhigh.mask = mask
        # self.xlow.mask = mask

        root =[]
        noroot = []
        for i in range(1,self.n):
            if self.parent[i] == 0:
                root.append(i)
            else:
                noroot.append(i)
        self.xrootid = np.array(root, dtype=int)
        self.xnorootid = np.array(noroot, dtype=int)
        self.r = self.xrootid.size

        self.solution_merge()

        self.xtime = np.array(self.solution, dtype=float) # vars+fixed times
        self.xvarid = np.array(self.map, dtype=int) #variable index
        self.xvar = self.xtime[self.xvarid] # vars only, send this to minimi
        self.xrate = np.zeros(self.n, dtype=float) # root rate stays zero forever
        self.xparid = np.array(self.parent, dtype=int) # parent index
        # self.r = len(self.xparid[self.xparid==0]) # how many children root has
        self.xsubs = np.array(self.subs, dtype=float) # substitutions
        # self.xrootmask = ma.masked_equal(self.xparid,0).mask # root children only

        # self.xconid = np.array(self.constrained, dtype=int) # only those directly cons'd
        self.xconid = np.array(self.map, dtype=int) # all the vars
        self.xlow = np.array(self.low, dtype=float)[self.xconid] # -"-
        self.xhigh = np.array(self.high, dtype=float)[self.xconid] # -"-


    def take(self):
        """
        Return ultrametric tree with ages and local rates
        """
        nsites = self._param.branch_length['nsites']
        for i in range(self.n):
            self.node[i].age = self.solution[i]
            #! PRETTY SURE this is wrong but have to match original....
            self.node[i].rate = self.xrate[i]/nsites
        return self._tree

    def guess(self):
        """
        Assign variables between low and high bounds.
        The guess will never touch the boundaries (at least 2% away).
        """
        # We will be modifying children high boundaries according to parent guess.
        # Copy array.high to keep these changes temporary
        window = self.high.copy()

        # Gather guesses here:
        variable = []

        # Start with the root if not fixed
        if self.age[0] is None:
            if all((self.low[0], self.high[0])):
                # Both boundaries exist, get a random point within
                high = self.high[0]
                low = self.low[0]
                diff = high - low
                shift = diff * random.uniform(0.02,0.98)
                age = high - shift
            elif self.low[0] is not None:
                #? Static percentages were used in original program...
                age = self.low[0] * 1.25
            elif self.high[0] is not None:
                #? Should we randomise all 3 cases?
                age = self.high[0] * 0.75
            else:
                # This could still diverge as long as there is an internal high boundary.
                # Find that and go higher still.
                age = apply_fun_to_list(max, self.high)
                if age is None: raise RuntimeError(
                    'This will never diverge, should have been caught by make_array()!')
                #? Even this might need to be randomised
                age *= 1.25
            # Window gets narrower for children and root age is saved
            window[0] = age
            variable.append(age)

        # Keep guessing from the top, restricting children as we go.
        for i in range(1,self.n):
            # Child is never older than parent
            window[i] = apply_fun_to_list(min,
                [window[i], window[self.parent[i]]])
            if self.age[i] == None:
                # This node is not fixed, assign a random valid age
                high = window[i]
                low = self.low[i]
                order = self.order[i]
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
        self.variable = variable

        self.solution_merge()
        #upd
        self.xvar = np.array(self.variable, dtype=float)
        self.xtime[self.xvarid] = self.xvar


    def perturb(self):
        """
        Shake up the values for a given guess, while maintaining feasibility
        """
        #! Make sure a guess exists in variable
        if not all(self.variable):
            raise RuntimeError('There is no complete guess to _perturb!')
        perturb_factor = self._param.general['perturb_factor']

        # Keep lower bound window for each variable
        window = [None] * self.v

        # Start iterating variables only from the bottom up
        # making sure the parent never gets younger than their children
        for j in reversed(range(0,self.v)):

            # j counts variables, i counts everything
            i = self.map[j]
            parent_position = self.parent[i]

            # Determine perturbation window first
            perturb_high = self.variable[j] * (1 + perturb_factor)
            perturb_low = self.variable[j] * (1 - perturb_factor)

            # Catch root, it has no parent so ignore this from upper boundary
            #? Can possibly move this outside
            if self.parent[i] != i:
                parent_age = self.solution[parent_position]
            else:
                parent_age = None

            high = apply_fun_to_list(min,
                [perturb_high, self.high[i], parent_age])

            low = apply_fun_to_list(max,
                [perturb_low, self.low[i], window[j]])

            age = random.uniform(low,high)

            self.variable[j] = age

            # If parent is a variable, adjust its window
            if self.age[parent_position] is None:
                parent_variable = self.unmap[parent_position]
                window_current = window[parent_variable]
                window_new = apply_fun_to_list(max, [age,window_current])
                window[parent_variable] = window_new

        self.solution_merge()
        #upd
        self.xvar = np.array(self.variable, dtype=float)
        self.xtime[self.xvarid] = self.xvar



##############################################################################
### Results

class AnalysisResults(dict):
    """
    Bundle output here.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __repr__(self):
        if self.keys():
            m = max(map(len, list(self.keys()))) + 1
            return '\n'.join([k.rjust(m) + ': ' + repr(v)
                              for k, v in sorted(self.items())])
        else:
            return self.__class__.__name__ + "()"

    def __dir__(self):
        return list(self.keys())

    def __init__(self, tree):
        self.tree = tree

        node = []
        age = []
        rate = []
        for n in tree.preorder_node_iter():
            node.append(n.label)
            age.append(n.age)
            rate.append(n.rate)
        self.table = {
            'n': len(node),
            'Node': node,
            'Age': age,
            'Rate': rate,
            }
        self.chronogram = tree.clone(depth=1)
        for node in self.chronogram.preorder_node_iter_noroot():
            node.edge_length = node.parent_node.age - node.age
        self.chronogram.seed_node.edge_length = None
        extensions.strip(self.chronogram)

    def print(self, columns=None):
        if columns is None:
            columns = ['Node', 'Age', 'Rate']
        formats = {
            'Node': '{:12.10}',
            'Age': '{:>12.4f}',
            'Rate': '{:>12.4e}',
            }
        headers = {
            'Node': '{:12}',
            'Age': '{:>9}   ',
            'Rate': '   {:10}',
            }
        header = '\n\t'
        for column in columns:
            header += headers[column].format(column)
        print(header)
        print('-' * (len(header) + 12))
        for index in range(self.table['n']):
            row = '\t'
            for column in columns:
                value = self.table[column][index]
                row += formats[column].format(value)
            print('{}\t'.format(row))
        print('\n')


##############################################################################
### Analysis

class Analysis:
    """
    All the work happens here
    """
    #? Consider locking attributes with __slots__ or @dataclass

    def __init__(self, tree=None):
        random.seed(1) #! remove the 1 later !!!!
        self.param = params.Param()
        self._array = Array(self.param)
        if tree is None:
            self._tree = None
        else:
            self.tree = tree

    @property
    def tree(self):
        """User can edit tree before run()"""
        return self._tree

    @tree.setter
    def tree(self, phylogram):
        self._tree = phylogram.clone(depth=1)
        extensions.extend(self._tree)
        self._tree.is_rooted = True
        self._tree.ground()
        self._tree.collapse()


    ##########################################################################
    ### Method function generators

    def _build_objective_nprs(self):
        """Generate NPRS objective function"""

        logarithmic = self.param.nprs['logarithmic'] #! NOT USED
        exponent = self.param.nprs['exponent'] #! NOT USED
        largeval = self.param.general['largeval']
        array = self._array

        #? these can probably be moved downstairs? doesnt seem to make a diff
        xtime = array.xtime
        xparid = array.xparid
        xvarid = array.xvarid
        xrate = array.xrate
        xsubs = array.xsubs
        # xrootmask = array.xrootmask
        xrootid = array.xrootid
        xnorootid = array.xnorootid
        r = array.r

        def objective_nprs(x):
            """
            Ref Sanderson, Minimize neighbouring rates
            """
            # obj
            xtime[xvarid] = x # put new vars inside time

            xpartime = xtime[xparid] # parent times
            xdiftime = xpartime - xtime # time diff
            if xdiftime[xdiftime<=0][1:].size != 0: # ignore root
                return largeval
            xrate[1:] = xsubs[1:]/xdiftime[1:]
            xparrate = xrate[xparid]
            xrateroot = xrate[xrootid]
            sumrootrate = xrateroot.sum()
            sumrootrate *= sumrootrate
            xrateroot *= xrateroot
            sumrootratesquared = xrateroot.sum()
            xdifrate = xrate-xparrate
            xdifrate *= xdifrate
            xdifratemasked = xdifrate[xnorootid]
            sumratesquared = xdifratemasked.sum()
            w = (sumrootrate - r*sumrootratesquared)/r + sumratesquared
            return w
            # return 0

        return objective_nprs


    def _build_barrier_penalty(self):
        """Generate penalty function"""

        largeval = self.param.general['largeval']
        array = self._array
        xtime = array.xtime
        xconid = array.xconid
        xhigh = array.xhigh
        xlow = array.xlow

        def barrier_penalty(x):
            """
            Keep variables away from bounds
            """
            # pen

            xcons = xtime[xconid]
            xl = xcons - xlow
            xh = xhigh - xcons
            t = xh[(xl<0)|(xh<0)]
            if t.size != 0:
                return largeval
            xa = 1/xl + 1/xh
            return xa.sum()

        return barrier_penalty


    ##########################################################################
    ### Algorithms

    def _algorithm_powell(self):
        """
        Repeat as necessary while relaxing barrier
        """
        objective = None
        array = self._array
        result = None
        # Use the appropriate algorithm
        if hasattr(self, '_build_objective_' + self.param.method):
            objective = getattr(self, '_build_objective_' + self.param.method)()
        else:
            raise ValueError('No such algorithm: {0}'.format(self.param.method))

        variable_tolerance = self.param.powell['variable_tolerance']
        function_tolerance = self.param.powell['function_tolerance']

        if self.param.barrier['manual'] == True:

            # Adds a barrier_penalty to the objective function
            # to keep solution variables away from their boundaries.
            # We are interested in the pure objective function value.
            # Relax the barrier penalty factor with each iteration,
            # while also perturbing the variables

            barrier_penalty = self._build_barrier_penalty()

            factor = self.param.barrier['initial_factor']
            kept_value = objective(array.xvar)

            for b in range(self.param.barrier['max_iterations']):

                print('Barrier iteration: {0}'.format(b))

                result = optimize.minimize(
                    lambda x: objective(x) + factor*barrier_penalty(x),
                    array.xvar, method='Powell',
                    options={'xtol':variable_tolerance,'ftol':function_tolerance})

                array.variable = list(result.x)
                array.xvar = np.array(result.x, dtype=float)

                new_value = objective(array.xvar)

                if new_value == 0:
                    break

                tolerance = abs((new_value - kept_value)/new_value)

                if tolerance < self.param.barrier['tolerance']:
                    break
                else:
                    kept_value = new_value
                    factor *= self.param.barrier['multiplier']
                    self._array.perturb()

        else:
                result = optimize.minimize(objective, array.variable,
                    method='Powell', bounds=array.bounds,
                    options={'xtol':variable_tolerance,'ftol':function_tolerance})

                array.variable = list(result.x)

        return result.fun


    ##########################################################################
    ### Utility

    def print_tree(self):
        """Quick method to print the tree"""
        self.tree.print_plot(show_internal_node_labels=True)


    ##########################################################################
    ### Optimization

    def _optimize(self):
        """
        Applies the selected algorithm to the given array
        over multiple guesses, keeping the best
        """

        #! This is a good place to output warnings etc
        #! Also to make_array
        array = self._array
        kept_min = None
        kept_variable = None
        kept_rate = None

        for g in range(self.param.general['number_of_guesses']):

            self._array.guess()

            print('Guess {0}: {1}\n'.format(g, array.variable))

            # Call the appropriate optimization method
            if hasattr(self, '_algorithm_' + self.param.algorithm):
                new_min = getattr(self, '_algorithm_' + self.param.algorithm)()
            else:
                raise ValueError('No implementation for algorithm: {0}'.format(self.param.algorithm))

            print('\nLocal solution:\t {0:>12.4e}\n{1}\n'.format(new_min,array.solution))

            kept_min = apply_fun_to_list(min, [kept_min, new_min])
            if kept_min == new_min:
                kept_variable = array.xvar
                kept_rate = array.xrate

        array.variable = kept_variable
        array.xvar = kept_variable
        array.rate = kept_rate
        array.xrate = kept_rate
        array.solution_merge()
        print('\nBest solution:\t {0:>12.4e}\n{1}\n'.format(kept_min,array.solution))
        return kept_variable


    def run(self):
        """
        This is the only thing the user needs to run.
        """
        if self.tree is None:
            raise ValueError('No tree to optimize.')
        if len(self.tree.nodes()) < 1:
            raise ValueError('Tree must have at least one child.')
        self._array.make(self.tree)
        self._optimize()
        tree = self._array.take()
        self._results = AnalysisResults(tree)
        return self._results

    @classmethod
    def quick(cls, tree, scalar=True):
        """
        Run analysis without setting constraints or params
        ultrametric_tree = core.Analysis.quick(my_tree)
        """
        analysis = cls(tree)
        analysis.param.general['scalar'] = scalar
        res = analysis.run()
        return res.tree
