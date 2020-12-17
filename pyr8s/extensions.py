#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Extend dendropy trees with utility functions and attributes.
"""

import dendropy

##############################################################################
### Utility function definitions

class NodePlus(dendropy.Node):

    decorator = '[{}]'

    @property
    def label(self):
        try:
            return self.taxon.label
        except:
            if self._label is not None and self._label != '':
                return self._label
            elif self.index is not None:
                return self.decorator.format(self.index)
            else:
                return self.decorator.format('?')

    @label.setter
    def label(self, value):
        self._label = value

    @classmethod
    def extend(cls, node):
        """Convert from dendropy.Node"""
        node._label = node.label
        node.__class__ = cls
        node.index = None
        node.order = None
        node.fix = None
        node.min = None
        node.max = None
        node.rate = None
        node.subs = None

    @classmethod
    def strip(cls, node):
        """Revert to dendropy.Node"""
        del node.index
        del node.order
        del node.fix
        del node.min
        del node.max
        del node.rate
        del node.subs
        node.__class__ = dendropy.Node
        node.label = node._label
        del node._label

    def child_node_reversed_iter(self, filter_fn=None):
        """Reversed order"""
        for node in reversed(self._child_nodes):
            if filter_fn is None or filter_fn(node):
                yield node

    def add_child_after(self, node, child):
        """Insert child in list of children immediately after node index"""
        assert child is not self, "Cannot add node as child of itself"
        assert self._parent_node is not child, "Cannot add a node's parent as its child: remove the node from its parent's child set first"
        index = self._child_nodes.index(node) + 1
        child._parent_node = self
        if child not in self._child_nodes:
            self._child_nodes.insert(index, child)
        return child


class TreePlus(dendropy.Tree):

    def collapse(self, throw=False):
        """
        Remove edges with zero length.
        Prints warning or raises error depending on flag.
        """
        collapsed_constraints = self._collapse_inner()
        if collapsed_constraints != []:
            if not throw:
                print('WARNING: Collapsed nodes with constraints:')
                for n in collapsed_constraints:
                    print('* {0}: fix={1}, min={2}, max={3}'.
                        format(n.label, n.fix, n.min, n.max))
                print('')
            else:
                raise RuntimeError('Collapsed nodes with constraints: {}'.
                    format(collapsed_constraints))

    def _collapse_inner(self):
        """
        Remove edges with zero length.
        Return a list with any constrained nodes that were pruned.
        """
        remove = []
        collapsed_constraints = []

        # Children before parent, ensures removal is done in proper order
        for node in self.postorder_node_iter_noroot():
            #? Maybe consider a minimum length too
            if node.edge_length is None or node.subs == 0:
                remove.append(node)
                if node.fix is not None or node.min is not None or node.max is not None:
                    collapsed_constraints.append(node)

        # Remove the nodes, parents inherit children
        for node in remove:
            # Constraints passed to parents and children
            if node.fix is not None:
                inherit_up = node.fix
                inherit_down = node.fix
            else:
                inherit_up = node.max
                inherit_down = node.min
            parent = node.parent_node
            for child in node.child_node_reversed_iter():
                parent.add_child_after(node, child)
                if inherit_down is not None:
                    if child.max is not None:
                        child.max = min(child.max, inherit_down)
                    if child.max is None and child.fix is None:
                        child.max = inherit_down
            parent.remove_child(node)
            if inherit_up is not None:
                if parent.min is not None:
                    parent.min = max(parent.min, inherit_up)
                if parent.min is None and parent.fix is None:
                    parent.min = inherit_up

        return collapsed_constraints

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
        """Assign node indexes according to BF traversal order"""
        for count, node in enumerate(self.preorder_node_iter()):
            node.index = count
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
        ancestor.taxon.label = str(mrca)
        ancestor.label = str(mrca)

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
        NodePlus.extend(node)

def strip(tree):
    """
    Remove extensions, reverting to pure dendropy.Tree
    """
    for node in tree.nodes():
        NodePlus.strip(node)
    tree.__class__ = dendropy.Tree
