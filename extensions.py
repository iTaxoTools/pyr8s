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

##############################################################################
### Class Attributes

# Extend Node attributes
#? is there a better way to do this?
dendropy.Node.index = None
dendropy.Node.order = None
dendropy.Node.fix = None
dendropy.Node.min = None
dendropy.Node.max = None

# Extend Tree with flag attributes
dendropy.Tree._indexed = None
dendropy.Tree._ordered = None


##############################################################################
### Utility function definitions

def _collapse(self):
    """
    Remove edges with zero length
    """

    # Collect nodes for deletion
    remove = []

    # Children before parent, ensures removal is done in proper order
    for node in self.postorder_node_iter_noroot():
        print(node.taxon)
        print(node.label)
        print(node.edge_length)
        print('***')
        #? Maybe consider a minimum length too
        if node.edge_length == None:
            remove.append(node)

    # Get rid of the node, parent inherits children
    for node in remove:
        parent = node.parent_node
        for child in node.child_node_iter():
            parent.add_child(child)
        parent.remove_child(node)

def _index(self):
    """
    Assign node indexes according to BF traversal order
    Nodes without named taxa will be given a new taxon named with their index
    Also label nodes with their taxon name
    """

    # Start from root and branch out
    for count, node in enumerate(self.preorder_node_iter()):
        print('traversing node: {0}'.format(count))
        node.index = count
        if node.taxon == None:
            node.taxon = self.taxon_namespace.new_taxon(str(count))
        print(node.taxon.label)
        node.label = node.taxon.label
    self._indexed = True

def _order(self):
    """
    Assign order to each node of tree
    where order is the max distance from the leaves
    """

    def _order_recurse(node):
        """For each node, get max order of children + 1"""

        if node.is_leaf():
            node.order = 0
            return 0

        max_child_order = 0
        for child in node.child_node_iter():
            some_order = _order_recurse(child)
            max_child_order = max(max_child_order, some_order)
        max_child_order += 1
        node.order = max_child_order
        return max_child_order

    _order_recurse(self.seed_node)
    self._ordered = True

def _label_mrca(self,mrca,labels):
    """
    Rename most recent common ancestor of given nodes
    Nodes are given with their label
    If a single node is given, it is renamed
    """
    nm = self.mrca(taxon_labels=labels)
    nm.taxon.label=mrca

def _persite(self, nsites, round_flag=False):
    """
    DEPRECATED
    Use this when branch lengths are in units of numbers of substitutions per site
    This will multiply each branch length, rounding by default
    """
    for node in self.preorder_node_iter():
        if node.edge_length != None:
            node.edge_length *= nsites
        if round_flag == True:
            node.edge_length = round(node.edge_length)

def _preorder_node_iter_noroot(self):
    """
    See Tree.preorder_node_iter, except this takes no filter and excludes root
    """
    stack = [n for n in reversed(self.seed_node._child_nodes)]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(n for n in reversed(node._child_nodes))

def _postorder_node_iter_noroot(self):
    """
    See Tree.postorder_node_iter, except this takes no filter and excludes root
    """
    stack = [(n, False) for n in reversed(self.seed_node._child_nodes)]
    while stack:
        node, state = stack.pop()
        if state:
            yield node
        else:
            stack.append((node, True))
            stack.extend([(n, False) for n in reversed(node._child_nodes)])



##############################################################################
### Class functions

setattr(dendropy.Tree, 'collapse', _collapse)
setattr(dendropy.Tree, 'index', _index)
setattr(dendropy.Tree, 'order', _order)
setattr(dendropy.Tree, 'label_mrca', _label_mrca)
setattr(dendropy.Tree, 'persite', _persite)
setattr(dendropy.Tree, 'preorder_node_iter_noroot', _preorder_node_iter_noroot)
setattr(dendropy.Tree, 'postorder_node_iter_noroot', _postorder_node_iter_noroot)
