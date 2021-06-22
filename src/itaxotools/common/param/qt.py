#-----------------------------------------------------------------------------
# Pyr8s - Divergence Time Estimation
# Copyright (C) 2021  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------


"""Param Widgets for PySide6"""

from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

import sys

class ParamField():

    def __init__(self, parent, key, field):
        parent.fields.append(self)
        self.key = key
        self.parent = parent
        self.field = field
        self.widget = None
        self.draw()
        self.set(value=field.value)

    def draw(self):
        self.widget = QtWidgets.QWidget()
        self.widget.setToolTip(self.field.doc)

    def set(self, value=None):
        if value is None:
            value = self.field.default
        self.value = value

    def get(self):
        return self.value


class PComboBox(QtWidgets.QComboBox):

    WIDTH = 100

    def wheelEvent(self, event):
        if self.hasFocus:
            event.ignore()
        else:
            self.wheelEvent(event)

    def sizeHint(self):
        s = super().sizeHint()
        return QtCore.QSize(self.WIDTH, s.height())


class ParamList(ParamField):

    def __init__(self, parent, key, field, validator=None):
        super().__init__(parent, key, field)

        for i, l in enumerate(field.data['labels']):
            self.widget.addItem(l, field.data['items'][i])

        self.widget.currentIndexChanged.connect(parent.parent.onChange)

    def draw(self):
        self.widget = PComboBox(parent=self.parent)
        self.widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)
        self.widget.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.label = QtWidgets.QLabel(self.field.label + ': ')
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)

        layout = self.parent.layout()
        row = self.parent.nextRow()
        layout.addWidget(self.label, row, 0)
        layout.addWidget(self.widget, row, 1)
        self.widget.setToolTip(self.field.doc)
        self.label.setToolTip(self.field.doc)

    def set(self, value=None):
        if value is None:
            value = self.field.default
        i = self.widget.findData(value)
        self.widget.setCurrentIndex(i)

    def get(self):
        return self.widget.currentData()


class ParamBool(ParamField):

    def __init__(self, parent, key, field, validator=None):
        super().__init__(parent, key, field)
        self.widget.stateChanged.connect(parent.parent.onChange)

    def draw(self):
        self.widget = QtWidgets.QCheckBox(parent=self.parent)
        self.widget.setText(self.field.label)
        layout = self.parent.layout()
        row = self.parent.nextRow()
        layout.addWidget(self.widget, row, 0, 1, 2)
        self.widget.setToolTip(self.field.doc)

    def set(self, value=None):
        if value is None:
            value = self.field.default
        self.widget.setChecked(value)

    def get(self):
        return self.widget.isChecked()


class PLineEdit(QtWidgets.QLineEdit):

    WIDTH = 100

    def sizeHint(self):
        s = super().sizeHint()
        return QtCore.QSize(self.WIDTH, s.height())



class ParamEntry(ParamField):

    def __init__(self, parent, key, field, validator=None):
        super().__init__(parent, key, field)
        if validator is not None:
            self.widget.setValidator(validator(self.widget))
        self.widget.textChanged.connect(parent.parent.onChange)


    def draw(self):
        self.widget = PLineEdit(parent=self.parent)
        self.widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Preferred)

        self.label = QtWidgets.QLabel(self.field.label + ': ')
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)

        layout = self.parent.layout()
        row = self.parent.nextRow()
        layout.addWidget(self.label, row, 0)
        layout.addWidget(self.widget, row, 1)
        self.widget.setToolTip(self.field.doc)
        self.label.setToolTip(self.field.doc)

    def set(self, value=None):
        if value is None:
            value = self.field.default
        self.widget.setText(str(value))

    def get(self):
        return self.widget.text()


class ParamInt(ParamEntry):

    def __init__(self, parent, key, field):
        super().__init__(parent, key, field, validator=QtGui.QIntValidator)

    def get(self):
        return int(self.widget.text())


class ParamFloat(ParamEntry):

    def __init__(self, parent, key, field):
        super().__init__(parent, key, field, validator=QtGui.QDoubleValidator)

    def get(self):
        return float(self.widget.text())


class ParamCategory(QtWidgets.QGroupBox):
    """Holds a group of parameters"""
    def __init__(self, parent, key, category):
        super().__init__(category.label)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum)

        parent.categories.append(self)
        self.key = key
        self.category = category
        self.parent = parent
        self.fields = []

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1000)
        layout.setColumnMinimumWidth(1, 100)
        self.setLayout(layout)
        self.row = 0

        parent.containerLayout.addWidget(self)

    def nextRow(self):
        row = self.row
        self.row += 1
        return row

class ParamContainer(QtWidgets.QWidget):
    """All Param widgets go here"""
    paramChanged = QtCore.Signal(object)
    def __init__(self, param=None, doc=True, reset=True):
        super().__init__()
        self.categories = []
        self.param = None

        self.drawContainer()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.scroll)
        layout.setContentsMargins(5, 5, 5, 5)

        if doc:
            self.drawDoc()
            layout.addWidget(self.doc)

        if param is not None:
            self.populate(param)

        if reset:
            self.drawResetButton()

        self.setLayout(layout)

    def drawContainer(self):
        container = QtWidgets.QWidget()
        containerLayout = QtWidgets.QVBoxLayout()
        containerLayout.setContentsMargins(5, 5, 5, 5)
        container.setLayout(containerLayout)
        container.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy(
                QtWidgets.QSizePolicy.PolicyFlag.ExpandFlag | QtWidgets.QSizePolicy.PolicyFlag.ShrinkFlag
            ))

        scroll = QtWidgets.QScrollArea()
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        scroll.sizeHint = container.sizeHint
        scroll.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum)

        self.scroll = scroll
        self.container = container
        self.containerLayout = containerLayout

    def drawDoc(self):
        doc = QtWidgets.QGroupBox()
        docLayout = QtWidgets.QVBoxLayout()
        docLayout.setContentsMargins(5, 5, 5, 5)
        doc.setLayout(docLayout)

        doc.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Minimum)

        object = QtWidgets.QLabel("Hover parameters for quick help. Refer to the r8s manual for more.")
        object.setWordWrap(True)
        docLayout.addWidget(object)

        self.doc = doc

    def drawResetButton(self):
        button = QtWidgets.QPushButton('Reset to defaults')
        button.clicked.connect(self.resetDefaults)
        button.setAutoDefault(False)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(button)
        box = QtWidgets.QGroupBox()
        box.setLayout(layout)

        box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Maximum)

        self.containerLayout.addWidget(box)

    def populate(self, param):
        """Create category and field widget"""
        widget_from_type = {
            'int': ParamInt,
            'float': ParamFloat,
            'list': ParamList,
            'bool': ParamBool,
            }
        self.param = param
        for category in param.keys():
            new_category = ParamCategory(self, category, param[category])
            for field in param[category].keys():
                widget_from_type[param[category][field].type](
                    new_category, field, param[category][field])

    def setParams(self, param):
        """Show and match a new ParamList"""
        for category in self.categories:
            for field in category.fields:
                param_field = param[category.key][field.key]
                field.field = param_field
                field.set(value=param_field.value)
            category.category = param[category.key]
        self.param = param

    def resetDefaults(self):
        """Reset to defaults"""
        for category in self.categories:
            for field in category.fields:
                field.set()

    def applyParams(self):
        """Apply all widget values as ParamField values"""
        try:
            for category in self.categories:
                for field in category.fields:
                    field.field.value = field.get()
        except ValueError:
            raise ValueError('Invalid value for parameter: ' +
                category.category.label + ': ' + field.field.label)

    def onChange(self):
        """Emit signal"""
        self.paramChanged.emit(self.sender())
