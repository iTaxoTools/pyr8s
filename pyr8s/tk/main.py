from tkinter import *
from tkinter import ttk
import dendropy

from .. import core

def show():
    tree = dendropy.Tree.get(path="/home/steven/py/pyr8s/tests/legacy_1", schema="nexus", suppress_internal_node_taxa=False)
    analysis = core.RateAnalysis(tree)
    root = Tk()
    ttk.Button(root, text="Hello World").grid()
    root.mainloop()
