#! /usr/bin/env python
# -*- coding: utf-8 -*-

from tkinter import *
from tkinter import ttk

_PARAM_WIDTH = 80

class ParamField:
    """Prototype Param with label and custom entry field"""

    def __init__(self, category, field, row):
        category.fields.append(self)
        self.parent = category.frame
        self.category = category
        self.field = field
        self.row = row
        self.var = self.var()
        self.var.trace_add('write', self.update)
        self.interface()
    def update(self, *args):
        try:
            self.field.value = self.get()
            self.valid()
        except ValueError:
            self.invalid()
            pass
    def valid(self):
        print('Set:', self.field.label, '=', self.field.value)
    def invalid(self):
        print('Set:', self.field.label, '= ?')
    def interface(self):
        pass
    def var(self):
        pass
    def get(self):
        pass

class ParamBool(ParamField):
    """Checkbox"""
    def interface(self):
        self.checkbutton = ttk.Checkbutton(self.parent, text=self.field.label,
            variable=self.var,
            onvalue=True, offvalue=False)
        self.parent.rowconfigure(self.row, weight=1, pad=2)
        self.checkbutton.grid(row=self.row, column=0, columnspan=2, sticky='nsw')
    def var(self):
        return BooleanVar(value=self.field.value)
    def get(self):
        return bool(self.var.get())

class ParamFieldEntry(ParamField):
    """With label and entry with fixed width"""
    def interface(self, entry_width=_PARAM_WIDTH):
        self.label = ttk.Label(self.parent, text=self.field.label+':  ')
        self.frame = ttk.Frame(self.parent, width=entry_width)
        self.entry = self.entry()
        self.parent.rowconfigure(self.row, weight=1, pad=10)
        self.frame.grid_propagate(0)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.label.grid(row=self.row, column=0, sticky='nswe')
        self.frame.grid(row=self.row, column=1, sticky='nswe')
        self.entry.grid(row=0, column=0, sticky='we')
        self.style()
    def style(self):
        self.style_valid = 'TEntry'
        self.style_invalid = 'Alert.TEntry'
    def valid(self):
        self.entry.configure(style=self.style_valid)
        super().valid()
    def invalid(self):
        self.entry.configure(style=self.style_invalid)
        super().invalid()
    def entry(self):
        pass

class ParamInt(ParamFieldEntry):
    """For integer parameters"""
    def entry(self):
        check = (self.frame.register(lambda v:
            re.match('^[0-9]*$', v) is not None), '%P')
        entry = ttk.Entry(self.frame, textvariable=self.var,
            validate='key', validatecommand=check)
        return entry
    def var(self):
        return StringVar(value=self.field.value)
    def get(self):
        return int(self.var.get())

class ParamFloat(ParamFieldEntry):
    """For float point parameters"""
    def entry(self):
        check = (self.frame.register(lambda v:
            re.match('^[0-9]*\.?[0-9]*(e(\-|\+)?[0-9]*)?$', v) is not None), '%P')
        entry = ttk.Entry(self.frame, textvariable=self.var,
            validate='key', validatecommand=check)
        return entry
    def var(self):
        return StringVar(value=self.field.value)
    def get(self):
        return float(self.var.get())

class ParamList(ParamFieldEntry):
    """For item list parameters"""
    def entry(self):
        entry = ttk.Combobox(self.frame, state='readonly',
            textvariable=self.var, values=self.field.data['labels'])
        entry.bind('<<ComboboxSelected>>', lambda e: e.widget.selection_clear())
        return entry
    def style(self):
        self.style_valid = 'TCombobox'
        self.style_invalid = 'Alert.TCombobox'
    def var(self):
        i = self.field.data['items'].index(self.field.value)
        return StringVar(value=self.field.data['labels'][i])
    def get(self):
        i = self.field.data['labels'].index(self.var.get())
        return self.field.data['items'][i]

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
    def __init__(self, parent, param=None):
        style = ttk.Style()
        style.configure('Alert.TCombobox', bordercolor='red')
        style.configure('Alert.TEntry', bordercolor='red')
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

        # def helloCallBack():
        #     print(param.algorithm.algorithm)
        # btn = ttk.Button(self.fdoc, text='Do it', command=helloCallBack)
        # btn.grid(row=0, column=1)
        # btn = ttk.Entry(self.fdoc, text='Do it')
        # btn.grid(row=0, column=0)
        lbl = ttk.Label(self.fdoc, text='Number of guesses:\n'+
            'How many times to repeat the analysis.\n'+
            'Different starting point each time.')
        lbl.grid(row=0, column=0, padx=10, pady=10)

        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=0)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.scrollbar.grid(row=0, column=1, padx=(5,0), sticky='nse')
        self.fdoc.grid(row=1, column=0, columnspan=2, pady=(5,5), sticky='nswe')

        if param is not None:
            self.populate(param)

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

    def populate(self, param):
        """Create categories and fields"""
        widget_from_type = {
            'int': ParamInt,
            'float': ParamFloat,
            'list': ParamList,
            'bool': ParamBool,
            }
        for i, category in enumerate(param.keys()):
            new_category = ParamCategory(self,
                i, param[category])
            for j, field in enumerate(param[category].keys()):
                widget_from_type[param[category][field].type](new_category,
                    param[category][field], j)
