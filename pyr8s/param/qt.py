#! /usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QLabel, QScrollArea, QGroupBox,
        QLineEdit, QComboBox, QCheckBox, QPushButton, QMessageBox,
        QHBoxLayout, QVBoxLayout, QFormLayout, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIntValidator, QDoubleValidator


class ParamField(QWidget):
    def __init__(self, parent, field):
        super().__init__()

        parent.fields.append(self)
        self.parent = parent
        self.field = field
        self.set()
        self.draw()

    def set(self, value=None):
        if value is None:
            value = self.field.default
        self.value = value

    def get(self):
        return self.value

    def draw(self):
        pass


class ParamList(QComboBox, ParamField):

    WIDTH = 100

    def __init__(self, parent, field, validator=None):
        super().__init__(parent, field)

        for i, l in enumerate(field.data['labels']):
            self.addItem(l, field.data['items'][i])

        self.set()

    def draw(self):
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.setFocusPolicy(Qt.StrongFocus)

        label = QLabel(self.field.label + ': ')
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        layout = self.parent.layout()
        row = self.parent.nextRow()
        layout.addWidget(label, row, 0)
        layout.addWidget(self, row, 1)

    def wheelEvent(self, event):
        if self.hasFocus:
            event.ignore()
        else:
            self.wheelEvent(event)

    def sizeHint(self):
        s = super().sizeHint()
        return QSize(self.WIDTH, s.height())

    def set(self, value=None):
        if value is None:
            value = self.field.default
        i = self.findData(value)
        self.setCurrentIndex(i)

    def get(self):
        return self.currentData()


class ParamBool(QCheckBox, ParamField):

    def __init__(self, parent, field, validator=None):
        super().__init__(parent, field)

    def draw(self):
        self.setText(self.field.label)
        layout = self.parent.layout()
        row = self.parent.nextRow()
        layout.addWidget(self, row, 0, 1, 2)

    def set(self, value=None):
        if value is None:
            value = self.field.default
        self.setChecked(value)

    def get(self):
        return self.isChecked()


class ParamEntry(QLineEdit, ParamField):

    WIDTH = 100

    def __init__(self, parent, field, validator=None):
        super().__init__(parent, field)

        if validator is not None:
            self.setValidator(validator(self))


    def draw(self):
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        label = QLabel(self.field.label + ': ')
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        layout = self.parent.layout()
        row = self.parent.nextRow()
        layout.addWidget(label, row, 0)
        layout.addWidget(self, row, 1)

    def sizeHint(self):
        s = super().sizeHint()
        return QSize(self.WIDTH, s.height())

    def set(self, value=None):
        if value is None:
            value = self.field.default
        self.setText(str(value))

    def get(self):
        return self.text()


class ParamInt(ParamEntry):

    def __init__(self, parent, field):
        super().__init__(parent, field, validator=QIntValidator)

    def get(self):
        return int(self.text())


class ParamFloat(ParamEntry):

    def __init__(self, parent, field):
        super().__init__(parent, field, validator=QDoubleValidator)

    def get(self):
        return float(self.text())


class ParamCategory(QGroupBox):
    """Holds a group of parameters"""
    def __init__(self, parent, category):
        super().__init__(category.label)

        parent.categories.append(self)
        self.category = category
        self.parent = parent
        self.fields = []
        # self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Preferred)

        layout = QGridLayout()
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

class ParamContainer(QWidget):
    """All Param widgets go here"""
    def __init__(self, param=None, doc=True, reset=True):
        super().__init__()

        self.categories = []
        self.param = None

        self.drawContainer()

        layout = QVBoxLayout()
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
        container = QWidget()
        containerLayout = QVBoxLayout()
        containerLayout.setContentsMargins(5, 5, 5, 5)
        container.setLayout(containerLayout)
        container.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Preferred)

        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)

        self.scroll = scroll
        self.containerLayout = containerLayout

    def drawDoc(self):
        doc = QGroupBox()
        docLayout = QVBoxLayout()
        docLayout.setContentsMargins(5, 5, 5, 5)
        doc.setLayout(docLayout)

        object = QLabel("This is a very helpful string about parameters "
                        "and how to use placeholders effectively.")
        object.setWordWrap(True)
        docLayout.addWidget(object)

        self.doc = doc

    def drawResetButton(self):
        button = QPushButton('Reset to defaults')
        button.clicked.connect(self.resetDefaults)
        layout = QVBoxLayout()
        layout.addWidget(button)
        box = QGroupBox()
        box.setLayout(layout)
        self.containerLayout.addWidget(box)

    def populate(self, param):
        """Create categories and fields"""
        widget_from_type = {
            'int': ParamInt,
            'float': ParamFloat,
            'list': ParamList,
            'bool': ParamBool,
            }
        self.param = param
        for category in param.keys():
            new_category = ParamCategory(self, param[category])
            for field in param[category].keys():
                widget_from_type[param[category][field].type](
                    new_category, param[category][field])

    def resetDefaults(self):
        for category in self.categories:
            for field in category.fields:
                field.set()

    def applyParams(self):
        try:
            for category in self.categories:
                for field in category.fields:
                    field.field.value = field.get()
        except ValueError:
            QMessageBox.warning(
                self, 'Invalid parameter',
                'Invalid value for parameter:\n' +
                category.category.label + ': ' + field.field.label,
                QMessageBox.Ok
            )
