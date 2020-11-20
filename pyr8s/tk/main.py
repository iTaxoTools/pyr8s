from tkinter import *
from tkinter import ttk
import dendropy

from .. import core

class Main:
    """Main screen"""

    def __init__(self, root):
        """Set everything up"""
        self.root = root #? is this needed?
        root.title("Pyr8s")
        root.geometry('300x300')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.tree = None
        self.analysis = None

        self.draw()

    def draw(self):
        """Create and place widgets"""

        s = ttk.Style()
        s.configure('My.TFrame', background="red")

        m = PanedWindow(self.root, orient=HORIZONTAL)
        f1 = ttk.Frame(m, style='My.TFrame')
        f2 = ttk.Frame(m, style='My.TFrame')
        l1 = ttk.Label(f1,text="left")
        l2 = ttk.Label(f2,text="right")
        sep = ttk.Separator(f2,orient=VERTICAL)
        # l1.grid(column=0, row=0, sticky="nswe")
        # l2.grid(column=0, row=0, sticky="nswe")

        sep.grid(column=0,row=0, sticky="wns")
        m.grid(column = 0, row = 0, sticky="nswe")
        f1.columnconfigure(0,weight=1)
        f1.rowconfigure(0,weight=1)
        f2.columnconfigure(0,weight=1)
        f2.rowconfigure(0,weight=1)
        m.add(f1, minsize="1cm")
        m.add(f2, minsize="1cm")

    def open(self, file):
        """Load tree from file"""
        try:
            self.tree = dendropy.Tree.get(path=file,
                schema="nexus", suppress_internal_node_taxa=False)
            self.analysis = core.RateAnalysis(self.tree)
            print("Loaded file: " + file)
        except FileNotFoundError as e:
            print("Failed to load file: " + str(e))


def show(file=None):
    """Entry point"""
    root = Tk()
    main = Main(root)
    if file is not None:
        main.open(file)
    root.mainloop()

    # s = ttk.Style()
    # s.configure('My.TFrame', background='red')
    #
    # content = ttk.Frame(root, padding=(3,3,12,12))
    # frame = ttk.Frame(content, style='My.TFrame', borderwidth=5, relief="ridge", width=200, height=100)
    # hilbl = ttk.Label(frame, background="yellow", text="Hi")
    # namelbl = ttk.Label(content, text="Name")
    # name = ttk.Entry(content)
    #
    # onevar = BooleanVar()
    # twovar = BooleanVar()
    # threevar = BooleanVar()
    #
    # onevar.set(True)
    # twovar.set(False)
    # threevar.set(True)
    #
    # one = ttk.Checkbutton(content, text="One", variable=onevar, onvalue=True)
    # two = ttk.Checkbutton(content, text="Two", variable=twovar, onvalue=True)
    # three = ttk.Checkbutton(content, text="Three", variable=threevar, onvalue=True)
    # ok = ttk.Button(content, text="Okay")
    # cancel = ttk.Button(content, text="Cancel")
    #
    # content.grid(column=0, row=0, sticky=(N, S, E, W))
    # frame.grid(column=0, row=0, columnspan=3, rowspan=2, sticky=(N, S, E, W))
    # hilbl.grid(column=0, row=0, padx=15)
    # namelbl.grid(column=3, row=0, columnspan=2, sticky=(N, W), padx=5)
    # name.grid(column=3, row=1, columnspan=2, sticky=(N,E,W), pady=5, padx=5)
    # one.grid(column=0, row=3)
    # two.grid(column=1, row=3)
    # three.grid(column=2, row=3)
    # ok.grid(column=3, row=3)
    # cancel.grid(column=4, row=3)
    #
    # root.columnconfigure(0, weight=1)
    # root.rowconfigure(0, weight=1)
    # frame.columnconfigure(0, weight=1)
    # frame.rowconfigure(0, weight=1)
    # content.columnconfigure(0, weight=3, minsize=100)
    # content.columnconfigure(1, weight=3)
    # content.columnconfigure(2, weight=3)
    # content.columnconfigure(3, weight=1)
    # content.columnconfigure(4, weight=1)
    # content.rowconfigure(1, weight=1)
