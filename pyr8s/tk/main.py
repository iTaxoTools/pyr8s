#! /usr/bin/env python
# -*- coding: utf-8 -*-

from tkinter import *
from tkinter import ttk
import dendropy
import re

from .. import core
from ..param import tk as ptk


def bind_scroll_wheel(canvas, frame):
    os = canvas.tk.call('tk', 'windowingsystem')
    if os == 'x11':
        canvas.bind_all('<Button-4>', lambda e:
            canvas.event_generate("<MouseWheel>",delta=1))
        canvas.bind_all('<Button-5>', lambda e:
            canvas.event_generate("<MouseWheel>",delta=-1))
    if os == 'win32':
        def _on_wheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), 'units')
    else:
        def _on_wheel(e):
            canvas.yview_scroll(int(-1*(e.delta)), 'units')
    def _bind_wheel(e):
        canvas.bind_all('<MouseWheel>', _on_wheel)
    def _unbind_wheel(e):
        canvas.unbind_all('<MouseWheel>')
    frame.bind('<Enter>',_bind_wheel)
    frame.bind('<Leave>',_unbind_wheel)


class Main:
    """Main screen"""

    def __init__(self, root):
        """Set everything up"""
        self.root = root #? is this needed?
        root.title('Pyr8s')
        root.geometry('854x480+0+0')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.analysis = core.RateAnalysis()

        self.draw()

    def draw(self):
        """Create and place widgets"""
        s = ttk.Style()
        s.theme_use('clam')
        s.configure('Red.TFrame', background='red')
        s.configure('Green.TFrame', background='green')
        s.configure('Blue.TFrame', background='blue')
        s.configure('Yellow.TFrame', background='yellow')
        s.configure('White.TFrame', background='white')
        # s.configure('Red.TFrame')
        # s.configure('Green.TFrame')
        # s.configure('Blue.TFrame')
        # s.configure('Yellow.TFrame')
        # s.configure('Visible.Panedwindow', background='red')

        _TOOLBAR_HEIGHT = 36
        _TOOLBAR_PAD = 6
        _FOOTER_HEIGHT = 22
        _RUN_HEIGHT = 36
        _PARAM_WIDTH = 100

        def draw_pane_right(parent):

            ftoolbar = ttk.Frame(parent, height=_TOOLBAR_HEIGHT, padding=(0,2))
            fgraph = ttk.Frame(parent, relief='ridge')
            ffoot = ttk.Frame(parent, height=_FOOTER_HEIGHT, padding=(0,2))
            stoolbar = ttk.Separator(parent, orient=HORIZONTAL)
            sfoot = ttk.Separator(parent, orient=HORIZONTAL)

            fleft = ttk.Frame(ftoolbar)
            fright = ttk.Frame(ftoolbar)

            bopen = ttk.Button(fleft, text='Open')
            bsave = ttk.Button(fleft, text='Save')
            bexport = ttk.Button(fleft, text='Export')
            blogs = ttk.Button(fright, text='Logs')
            lnote = ttk.Label(ffoot, text='Notification here.')

            ftoolbar.grid_propagate(0)
            ffoot.grid_propagate(0)
            ftoolbar.grid(row=0, column=0, sticky='nwe')
            # stoolbar.grid(row=1, column=0, sticky='we')
            fgraph.grid(row=2, column=0, pady=2, sticky='nswe')
            # sfoot.grid(row=3, column=0, sticky='we')
            ffoot.grid(row=4, column=0, sticky='swe')

            fleft.grid(row=0, column=0, sticky='nsw')
            fright.grid(row=0, column=1, sticky='nse')
            bopen.grid(row=0, column=0, padx=(0,_TOOLBAR_PAD), sticky='nswe')
            bsave.grid(row=0, column=1, padx=(0,_TOOLBAR_PAD), sticky='nswe')
            bexport.grid(row=0, column=2, padx=(0,_TOOLBAR_PAD), sticky='nswe')
            blogs.grid(row=0, column=0, padx=(0,0), sticky='nswe')
            lnote.grid(row=0, column=0, padx=(0,0), sticky='nsw')

            parent.rowconfigure(0, weight=0)
            parent.rowconfigure(1, weight=0)
            parent.rowconfigure(2, weight=1)
            parent.rowconfigure(3, weight=0)
            parent.rowconfigure(4, weight=0)
            ftoolbar.columnconfigure(0, weight=3)
            ftoolbar.columnconfigure(1, weight=1)
            ftoolbar.rowconfigure(0, weight=1)
            ffoot.columnconfigure(0, weight=1)
            ffoot.rowconfigure(0, weight=1)

            fleft.columnconfigure(0, weight=1)
            fleft.columnconfigure(1, weight=1)
            fleft.columnconfigure(2, weight=1)
            fleft.rowconfigure(0, weight=1)
            fright.columnconfigure(0, weight=1)
            fright.rowconfigure(0, weight=1)

        def draw_params(parent):

            widget_from_type = {
                'int': ptk.ParamInt,
                'float': ptk.ParamFloat,
                'list': ptk.ParamList,
                'bool': ptk.ParamBool,
                }

            param = self.analysis.param

            fparam = ttk.Frame(parent)
            fparam.grid(row=0, column=0, padx=5, pady=(5,0), sticky='nswe')
            parent.columnconfigure(0, weight=1)
            parent.rowconfigure(0, weight=1)

            container = ptk.ParamContainer(fparam, s)
            bind_scroll_wheel(container.canvas, container.scrollframe)

            for i, category in enumerate(param.keys()):
                print(category, param[category].label)
                new_category = ptk.ParamCategory(container,
                    i, param[category].label)
                for j, field in enumerate(param[category].keys()):
                    print(field, param[category][field].label)
                    widget_from_type[param[category][field].type](new_category,
                        j, param[category][field].label)

            # newf = ptk.ParamCategory(container, 0, 'BOOP')
            # ptk.ParamList(newf, 0, 'List box')
            # ptk.ParamInt(newf, 1, 'Int box')
            # ptk.ParamFloat(newf, 2, 'Float boxaaaaaaaaaaaaaaaaaa')
            # ptk.ParamBool(newf, 10, 'Check box')
            #
            # newf = ptk.ParamCategory(container, 3, '1')
            # ptk.ParamList(newf, 0, 'List box')
            # ptk.ParamInt(newf, 1, 'Int box')
            # ptk.ParamFloat(newf, 2, 'Float box')
            # ptk.ParamBool(newf, 10, 'Check box')
            #
            # newf = ptk.ParamCategory(container, 5, '2')
            # ptk.ParamList(newf, 0, 'List box')
            # ptk.ParamInt(newf, 1, 'Int box')
            # ptk.ParamFloat(newf, 2, 'Float boxy')
            # ptk.ParamBool(newf, 10, 'Check box')


        def draw_tabs(parent):

            ntabs = ttk.Notebook(parent)

            fconstr = ttk.Frame(ntabs)
            ftable = ttk.Frame(ntabs)
            fparam = ttk.Frame(ntabs)

            ntabs.add(fconstr, text='Constraints')
            ntabs.add(ftable, text='Tables')
            ntabs.add(fparam, text='Params')

            parent.columnconfigure(0, weight=1)
            parent.rowconfigure(0, weight=1)

            ntabs.grid(row=0, column=0, sticky='nswe')

            draw_params(fconstr)


        def draw_pane_left(parent):

            fhead = ttk.Frame(parent, height=_TOOLBAR_HEIGHT, padding=(0,2))
            ftabs = ttk.Frame(parent, padding=(2,2))
            frun = ttk.Frame(parent, padding=(2,2))
            ffoot = ttk.Frame(parent, height=_FOOTER_HEIGHT, padding=(0,2))
            sline = ttk.Separator(parent, orient=HORIZONTAL)

            lhead = ttk.Label(fhead, anchor='center', relief='ridge', text='Tree of Life')
            lfoot = ttk.Label(ffoot, text='Progress')
            brun = ttk.Button(frun, text='Run')

            fhead.grid_propagate(0)
            ffoot.grid_propagate(0)
            fhead.grid(row=0, column=0, sticky='nswe')
            # sline.grid(row=1, column=0, sticky='we')
            ftabs.grid(row=2, column=0, sticky='nswe')
            frun.grid(row=3, column=0, sticky='nswe')
            ffoot.grid(row=4, column=0, sticky='swe')

            # flhead.grid(row=0, column=0, sticky='nswe')
            lhead.grid(row=0, column=0, sticky='nswe')
            lfoot.grid(row=0, column=0)
            brun.grid(row=0, column=0, sticky='nswe')

            fhead.columnconfigure(0, weight=1)
            fhead.rowconfigure(0, weight=1)
            # flhead.columnconfigure(0, weight=1)
            # flhead.rowconfigure(0, weight=1)

            parent.columnconfigure(0, weight=1)
            parent.rowconfigure(0, weight=0)
            parent.rowconfigure(1, weight=0)
            parent.rowconfigure(2, weight=1)
            parent.rowconfigure(3, weight=0)
            parent.rowconfigure(4, weight=0)

            frun.columnconfigure(0, weight=1)
            ffoot.columnconfigure(0, weight=1)
            ffoot.rowconfigure(0, weight=1)

            draw_tabs(ftabs)


        def draw_panes(parent):

            pmain = ttk.PanedWindow(parent, orient=HORIZONTAL)
            fleft = ttk.Frame(pmain)
            fright = ttk.Frame(pmain)
            sline = ttk.Separator(fleft,orient=VERTICAL)

            # pmain['sashwidth'] = 10
            # pmain['handlepad'] = 30

            sline.grid(column=0,row=0, sticky='wns')
            pmain.grid(column = 0, row = 0, sticky='nswe')

            fleft.columnconfigure(0,weight=1)
            fleft.rowconfigure(0,weight=1)
            fright.columnconfigure(0,weight=1)
            fright.rowconfigure(0,weight=1)

            pmain.add(fleft)
            pmain.add(fright)
            # pmain.add(fleft, minsize=_PANE_L_MIN_SIZE)
            # pmain.add(fright, minsize=_PANE_R_MIN_SIZE)

            draw_pane_left(fleft)
            draw_pane_right(fright)

        draw_panes(self.root)

    def open(self, file):
        """Load tree from file"""
        try:
            self.analysis.tree = dendropy.Tree.get(path=file,
                schema='nexus', suppress_internal_node_taxa=False)
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
    # frame = ttk.Frame(content, style='My.TFrame', borderwidth=5, relief='ridge', width=200, height=100)
    # hilbl = ttk.Label(frame, background='yellow', text='Hi')
    # namelbl = ttk.Label(content, text='Name')
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
    # one = ttk.Checkbutton(content, text='One', variable=onevar, onvalue=True)
    # two = ttk.Checkbutton(content, text='Two', variable=twovar, onvalue=True)
    # three = ttk.Checkbutton(content, text='Three', variable=threevar, onvalue=True)
    # ok = ttk.Button(content, text='Okay')
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
