#! /usr/bin/env python
# -*- coding: utf-8 -*-

from tkinter import *
from tkinter import ttk

_PARAM_WIDTH = 80

class ParamInt:
    def __init__(self, category, row, field, entry_width=_PARAM_WIDTH):
        parent = category.frame
        category.fields.append(self)
        self.category = category
        self.field = field
        self.var = StringVar(value=field.value)
        def var_update(*args):
            try:
                field.value = int(self.var.get())
            except ValueError:
                pass
        self.var.trace_add('write', var_update)
        check = (parent.register(lambda v:
            re.match('^[0-9]*$', v) is not None), '%P')
        self.label = ttk.Label(parent, text=field.label+':  ')
        self.frame = ttk.Frame(parent, width=entry_width)
        self.entry = ttk.Entry(self.frame, textvariable=self.var,
            validate='key', validatecommand=check)
        parent.rowconfigure(row, weight=1, pad=10)
        self.frame.grid_propagate(0)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.label.grid(row=row, column=0, sticky='nswe')
        self.frame.grid(row=row, column=1, sticky='nswe')
        self.entry.grid(row=0, column=0, sticky='we')


class ParamFloat:
    def __init__(self, category, row, field, entry_width=_PARAM_WIDTH):
        parent = category.frame
        category.fields.append(self)
        self.category = category
        self.field = field
        self.var = StringVar(value=field.value)
        def var_update(*args):
            try:
                field.value = float(self.var.get())
            except ValueError:
                pass
        self.var.trace_add('write', var_update)
        check = (parent.register(lambda v:
            re.match('^[0-9]*\.?[0-9]*(e(\-|\+)?[0-9]*)?$', v) is not None), '%P')
        self.label = ttk.Label(parent, text=field.label+':  ')
        self.frame = ttk.Frame(parent, width=entry_width)
        self.entry = ttk.Entry(self.frame, textvariable=self.var,
            validate='key', validatecommand=check)
        parent.rowconfigure(row, weight=1, pad=10)
        self.frame.grid_propagate(0)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.label.grid(row=row, column=0, sticky='we')
        self.frame.grid(row=row, column=1, sticky='nswe')
        self.entry.grid(row=0, column=0, sticky='we')

class ParamList:
    def __init__(self, category, row, field, entry_width=_PARAM_WIDTH):
        parent = category.frame
        category.fields.append(self)
        self.category = category
        self.field = field
        i = field.data['items'].index(field.value)
        self.var = StringVar(value=field.data['labels'][i])
        def var_update(*args):
            try:
                i = field.data['labels'].index(self.var.get())
                field.value = field.data['items'][i]
            except ValueError:
                pass
        self.var.trace_add('write', var_update)
        self.label = ttk.Label(parent, text=field.label+':  ')
        self.frame = ttk.Frame(parent, width=entry_width)
        self.combo = ttk.Combobox(self.frame, state='readonly',
            textvariable=self.var, values=self.field.data['labels'])
        self.combo.bind('<<ComboboxSelected>>', lambda e: e.widget.selection_clear())
        parent.rowconfigure(row, weight=1, pad=10)
        self.frame.grid_propagate(0)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.label.grid(row=row, column=0, sticky='nswe')
        self.frame.grid(row=row, column=1, sticky='nswe')
        self.combo.grid(row=0, column=0, sticky='we')

class ParamBool:
    """Checkbox"""
    def __init__(self, category, row, field):
        parent = category.frame
        category.fields.append(self)
        self.category = category
        self.field = field
        self.var = BooleanVar(value=field.value)
        def var_update(*args):
            try:
                field.value = bool(self.var.get())
            except ValueError:
                pass
        self.var.trace_add('write', var_update)
        self.checkbutton = ttk.Checkbutton(parent, text=field.label,
            variable=self.var,
            onvalue=True, offvalue=False)
        parent.rowconfigure(row, weight=1, pad=2)
        self.checkbutton.grid(row=row, column=0, columnspan=2, sticky='nsw')

class ParamCategory:
    """Holds a group of parameters"""
    def __init__(self, container, row, category):
        self.fields = []
        container.categories.append(self)
        self.container = container
        parent = container.scrollframe
        pad = 0 if row == 0 else 10
        self.frame = ttk.Labelframe(parent, text='  '+category.label, padding=(5,5))
        self.frame.grid(row=row, column=0, pady=(pad,0), sticky='nwe')
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(row, weight=0)
        self.frame.columnconfigure(0, weight=10000)
        self.frame.columnconfigure(1, weight=1)


class ParamContainer:
    """All Param widgets go here"""
    def __init__(self, parent, style, param):
        self.categories = []
        self.parent = parent
        self.canvas = Canvas(parent, height=0, width=0, highlightthickness=0,
            bg=style.lookup('TFrame', 'background'))
        self.scrollbar = ttk.Scrollbar(parent, orient='vertical',
            command=self.canvas.yview)
        self.scrollframe = ttk.Frame(self.canvas, padding=(0,0,1,0))
        self.iid = self.canvas.create_window((0,0), window=self.scrollframe, anchor='nw')
        self.fdoc = ttk.Frame(parent, relief='ridge')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        #! These DO call each other and stop when canvas is set to
        #  the same width as it already has... could this be bad later?
        self.scrollframe.bind('<Configure>', self._event_frame)
        self.canvas.bind('<Configure>', self._event_canvas)
        self.fdoc.bind('<Configure>', self._event_doc)


        def helloCallBack():
            print(param.algorithm.algorithm)
        btn = ttk.Button(self.fdoc, text='Do it', command=helloCallBack)
        btn.grid(row=0, column=1)

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=0)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.scrollbar.grid(row=0, column=1, padx=(5,0), sticky='nse')
        self.fdoc.grid(row=1, column=0, columnspan=2, pady=(5,5), sticky='nswe')

    def _event_frame(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        self.canvas.configure(width=self.scrollframe.winfo_width())

    def _event_canvas(self, e):
        self.canvas.itemconfig(self.iid, width=self.canvas.winfo_width())
        if e.height >= self.scrollframe.winfo_reqheight():
            self.scrollbar.grid_remove()
            self.canvas.configure(height=self.scrollframe.winfo_reqheight())
            self.parent.rowconfigure(1, weight=10000)

    def _event_doc(self, e):
        if (e.height < self.fdoc.winfo_reqheight()-1):
            self.canvas.configure(height=self.scrollframe.winfo_reqheight())
            self.parent.rowconfigure(1, weight=0)
            self.scrollbar.grid()

widget_from_type = {
    'int': ParamInt,
    'float': ParamFloat,
    'list': ParamList,
    'bool': ParamBool,
    }
