#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Parameter classes for use by core.Analysis class.
Parameter declarations and defaults are loaded from a json file.

Interactive python console example:
(assume ParamList param)

Browse available categories:
>>> param.keys()

Browse category 'general':
>>> param.general.keys()

Get the value of a specific field:
>>> f = param.general.scalar

Set the value of a specific field:
>>> param.general.scalar = True

Access field documentation:
>>> param.general['scalar'].doc
"""

import importlib.resources
import json

class ParamField():
    """Information about this parameter"""

    def __repr__(self):
        return '(' + str(self.label) + ': ' + str(self.value) + ')'

    def __dir__(self):
        return list(vars(self))

    def __init__(self, dictionary):
        self.order = dictionary['order']
        self.label = dictionary['label']
        self.doc = dictionary['doc']
        self.type = dictionary['type']
        self.default = dictionary['default']

        if 'meta' in dictionary.keys():
            self.meta = dictionary['meta']
        else:
            self.meta = {}

        self.value = dictionary['default']

class ParamCategory(dict):
    """Dictionary of fields belonging to this category."""

    def __getattr__(self, name):
        try:
            return self[name].value
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self.keys():
            try:
                self[name].value = value
            except KeyError:
                raise AttributeError(name)
        else:
            object.__setattr__(self, name, value)

    def __repr__(self):
        if self.keys():
            m = max(map(len, list(self.keys()))) + 1
            return '\n'.join([k.rjust(m) + ': ' + repr(v)
                              for k, v in sorted(self.items())])
        else:
            return self.__class__.__name__ + "()"

    def __dir__(self):
        return list(self.keys())

    def __init__(self, dictionary):
        self.label = dictionary['label']
        self.order = dictionary['order']
        for k in dictionary['fields'].keys():
            self[k] = ParamField(dictionary['fields'][k])


class ParamList(dict):
    """Dictionary of all categories."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __repr__(self):
        if self.keys():
            m = max(map(len, list(self.keys()))) + 1
            return '\n'.join([k.rjust(m) + ': ' + repr(v)
                              for k, v in sorted(self.items())])
        else:
            return self.__class__.__name__ + "()"

    def __dir__(self):
        return list(self.keys())

    def __init__(self):
        with importlib.resources.open_text(__package__, 'params.json') as data:
            dictionary = json.load(data)
        for k in dictionary.keys():
            self[k] = ParamCategory(dictionary[k])
