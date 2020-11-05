#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Extend dendropy trees with utility functions and attributes.
"""

import dendropy

##############################################################################
### Utility function definitions

class TreePlus(dendropy.Tree):

    def collapse(self):
        """
        Remove edges with zero length
        """

        # Collect nodes for deletion
        remove = []

        # Children before parent, ensures removal is done in proper order
        for node in self.postorder_node_iter_noroot():
            #? Maybe consider a minimum length too
            if node.edge_length is None or node.subs == 0:
                remove.append(node)

        # Get rid of the node, parent inherits children
        for node in remove:
            parent = node.parent_node
            for child in node.child_node_iter():
                parent.add_child(child)
            parent.remove_child(node)

    def calc_subs(self, multiplier, doround):
        """
        Set substitutions for each node
        """
        for node in self.postorder_node_iter_noroot():
            length = node.edge_length
            if length is None:
                raise ValueError('Null length for node {0}'.
                    format(node.label))
            if length <= 0:
                length = 0
            if multiplier is not None:
                length *= multiplier
            if doround == True:
                length = round(length)
            node.subs = length

    def ground(self):
        """
        Fix leaf age to zero if no calibrations exist
        """
        for node in self.postorder_node_iter_noroot():
            if node.is_leaf() and not any([node.fix, node.max, node.min]):
                node.fix = 0

    def index(self):
        """
        Assign node indexes according to BF traversal order
        Nodes without named taxa will be given a new taxon named with their index
        Also label nodes with their taxon name
        """

        # Start from root and branch out
        for count, node in enumerate(self.preorder_node_iter()):
            # print('traversing node: {0}'.format(count))
            node.index = count
            if node.taxon == None:
                node.taxon = self.taxon_namespace.new_taxon(str(count))
            # print(node.taxon.label)
            node.label = node.taxon.label
        self._indexed = True

    def order(self):
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

    def label_mrca(self,mrca,labels):
        """
        Rename most recent common ancestor of given nodes
        Nodes are given with their label
        If a single node is given, it is renamed
        Create the taxon if needed.
        """
        ancestor = self.mrca(taxon_labels=labels)
        if ancestor.taxon == None:
            ancestor.taxon = self.taxon_namespace.new_taxon(str(mrca))
        ancestor.taxon.label = mrca

    def persite(self, nsites, round_flag=False):
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

    def preorder_node_iter_noroot(self):
        """
        See Tree.preorder_node_iter, except this takes no filter and excludes root
        """
        stack = [n for n in reversed(self.seed_node._child_nodes)]
        while stack:
            node = stack.pop()
            yield node
            stack.extend(n for n in reversed(node._child_nodes))

    def postorder_node_iter_noroot(self):
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
### Extension

def extend(tree):
    """
    Extend given tree with node attributes and tree functions
    """
    tree.__class__ = TreePlus
    for node in tree.nodes():
        node.index = None
        node.order = None
        node.fix = None
        node.min = None
        node.max = None
        node.rate = None
        node.subs = None

def strip(tree):
    """
    Remove extensions, reverting to pure dendropy.Tree
    """
    tree.__class__ = dendropy.Tree
    for node in tree.nodes():
        del node.index
        del node.order
        del node.fix
        del node.min
        del node.max
        del node.rate
        del node.subs
