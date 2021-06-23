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


"""Custom PySide6 widgets for pyr8s"""

from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtGui

import re


##############################################################################
### Phylogenetic Trees

class TreeWidgetPhylogenetic(QtWidgets.QTreeWidget):
    """Styled to draw the branches of phylogenetic trees."""
    def __init__(self):
        super().__init__()
        self._searchSelecting = False
        self.selectionModel().selectionChanged.connect(
            self._onSelectionChanged)
        # self.itemActivated.connect(self.editItem)
        palette = QtGui.QGuiApplication.palette()
        self.colorSolid = palette.color(QtGui.QPalette.Shadow)
        self.colorDisabled = palette.color(QtGui.QPalette.Midlight)
        self.colorSelected = palette.color(QtGui.QPalette.HighlightedText)
        self.colorAlter = palette.color(QtGui.QPalette.AlternateBase).lighter(105)
        self.radiusLeaf = 3
        self.radiusInternal = 5
        self.branchOffset = 1
        self.setIndentation(16)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(0,
            QtWidgets.QHeaderView.Stretch)
        # QtCore.QTimer.singleShot(0, lambda:
        #     self.header().setSectionResizeMode(0,
        #         QtWidgets.QHeaderView.Interactive))
        self.setUniformRowHeights(True)
        self.setStyleSheet(
            """
            QTreeView {
                show-decoration-selected: 1;
            }
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: none;
            }
            QTreeView {
                alternate-background-color: """+self.colorAlter.name()+""";
            }
            QTreeView::item:selected:active,
            QTreeView::item:selected:!active,
            QTreeView::branch:selected:active,
            QTreeView::branch:selected:!active {
                color: """+self.colorSelected.name()+""";
                background: palette(Highlight);
            }
            QTreeView::branch:has-siblings:adjoins-item,
            QTreeView::branch:!has-children:!has-siblings:adjoins-item,
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings,
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings  {
                    border-image: none;
                    image: none;
            }
            """
            )


    # def scrollTo(self, index, hint):
    #     """Overloaded to prevent horizontal scroll on item select"""
    #     pass

    def setItemsDisabled(self, disable):
        """Disabled items but scrollbars remain enabled"""
        topItem = self.topLevelItem(0)
        if topItem is not None:
            topItem.setDisabled(disable)

    def idealWidth(self):
        """How much space is needed for all contents to be shown"""
        self.header().setSectionResizeMode(0,
            QtWidgets.QHeaderView.ResizeToContents)
        widthTree = self.viewportSizeHint().width()
        self.header().setSectionResizeMode(0,
            QtWidgets.QHeaderView.Stretch)
        # QtCore.QTimer.singleShot(0, lambda:
        #     self.header().setSectionResizeMode(0,
        #         QtWidgets.QHeaderView.Interactive))
        widthScrollbar = QtWidgets.QApplication.style().pixelMetric(
            QtWidgets.QStyle.PM_ScrollBarExtent)
        widthPadding = 30
        return widthTree+widthScrollbar+widthPadding

    def _onSelectionChanged(self, selected, deselected):
        """Calls onSelect with selected data"""
        if not self._searchSelecting:
            data = {}
            for index in selected.indexes():
                data[index.column()] = index.data()
            if len(data) > 0:
                self.onSelect(data)

    def onSelect(self, data):
        """Overload to do something with selection"""
        pass

    def searchSelect(self, what, flag=QtCore.Qt.MatchContains):
        self._searchSelecting = True
        if what == '':
            self.clearSelection()
        else:
            self.clearSelection()
            found = self.findItems(what, flag | QtCore.Qt.MatchRecursive)
            for item in found:
                item.setSelected(True)
            if len(found) > 0:
                self.scrollToItem(found[-1])
        self._searchSelecting = False

    def drawBranches(self, painter, rect, index):
        """Manually paint branches and nodes"""
        super().drawBranches(painter, rect, index)

        rect.setRight(rect.right() + self.branchOffset)

        indent = self.indentation()
        item = self.itemFromIndex(index)

        color = None
        if item.isSelected():
            color = self.colorSelected
        elif item.isDisabled():
            color = self.colorDisabled
        else:
            color = self.colorSolid

        solidPen = QtGui.QPen(color)
        solidPen.setWidth(2)
        painter.setBrush(color)
        painter.setPen(solidPen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        parent = item.parent()
        next = None
        if parent is not None:
            i = parent.indexOfChild(item)
            next = parent.child(i+1)
        child = item.child(0)

        isExpanded = item.isExpanded()
        hasChildren = child is not None
        hasMoreSiblings = next is not None

        # Paint own Node first
        segment = QtCore.QRect(rect)
        segment.setLeft(rect.right() - indent)
        if not hasChildren:
            radius = self.radiusLeaf
            center = segment.center()
            painter.drawEllipse(center, radius, radius)
            left = QtCore.QPoint(center.x()-segment.width()/2, center.y())
            leftMid = QtCore.QPoint(center.x()-radius, center.y())
            painter.drawLine(left, leftMid)
        else:
            radius = self.radiusInternal
            center = segment.center()
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)
            if isExpanded:
                bottom = QtCore.QPoint(center.x(), center.y()+segment.height()/2+1)
                bottomMid = QtCore.QPoint(center.x(), center.y()+radius)
                painter.drawLine(bottom, bottomMid)
            else:
                painter.setBrush(color)
                painter.drawEllipse(center, 1, 1)
            if parent is None:
                return
            left = QtCore.QPoint(center.x()-segment.width()/2, center.y())
            leftMid = QtCore.QPoint(center.x()-radius, center.y())
            painter.drawLine(left, leftMid)

        # Branch towards direct parent
        segment.moveLeft(segment.left() - indent)
        if segment.right() < 0:
            return
        if hasMoreSiblings:
            center = segment.center()
            right = QtCore.QPoint(center.x()+segment.width()/2, center.y())
            painter.drawLine(center, right)
            top = QtCore.QPoint(center.x(), segment.top()+1)
            bottom = QtCore.QPoint(center.x(), segment.bottom()+1)
            painter.drawLine(top, bottom)
        else:
            center = segment.center()
            right = QtCore.QPoint(center.x()+segment.width()/2, center.y())
            painter.drawLine(center, right)
            top = QtCore.QPoint(center.x(), segment.top()+1)
            painter.drawLine(top, center)

        # Branch extensions for ancestors
        segment.moveLeft(segment.left() - indent)
        item = parent
        while parent is not None:
            if segment.right() < 0:
                return
            parent = item.parent()
            next = None
            if parent is not None:
                i = parent.indexOfChild(item)
                next = parent.child(i+1)
            hasMoreSiblings = next is not None
            if hasMoreSiblings:
                center = segment.center()
                top = QtCore.QPoint(center.x(), segment.top()+1)
                bottom = QtCore.QPoint(center.x(), segment.bottom()+1)
                painter.drawLine(top, bottom)
            segment.moveLeft(segment.left() - indent)
            item = parent


class TreeWidgetNodeResults(QtWidgets.QTreeWidgetItem):
    """Analysis results on an extended dendropy tree"""
    def __init__(self, parent, node):
        """
        Creates a widget from a dendropy node and adds it to the parent.
        Recursively creates children widgets from children nodes.
        """
        super().__init__(parent)
        self.node = node
        label = str(node.label)
        age = '-' if node.age is None else '{:>1.2f}'.format(node.age)
        rate = '-' if node.rate is None else '{:>1.2e}'.format(node.rate)
        if node.rate == 0:
            rate = ' 0.00e-00'
        isMinMax = node.min is not None or node.max is not None
        isFixed = node.fix is not None
        if isFixed:
            type = '\u2219'
        elif isMinMax:
            type = '\u2217'
        else:
            type = ' '
        self.setText(0, label)
        self.setText(1, age)
        self.setText(2, rate)
        self.setText(3, type)
        self.setTextAlignment(1, QtCore.Qt.AlignRight)
        self.setTextAlignment(2, QtCore.Qt.AlignRight)
        self.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.setFlags(QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsEditable)
        for child in node.child_node_iter():
            TreeWidgetNodeResults(self, child)
        self.setExpanded(True)


class TreeWidgetNodeConstraints(QtWidgets.QTreeWidgetItem):
    """Constraints on an extended dendropy tree"""
    def __init__(self, parent, node):
        """
        Creates a widget from a dendropy node and adds it to the parent.
        Recursively creates children widgets from children nodes.
        Updates node when values are changed.
        """
        super().__init__(parent)
        self.node = node
        label = str(node.label)
        min = '-' if node.min is None else str(node.min)
        max = '-' if node.max is None else str(node.max)
        fix = '-' if node.fix is None else str(node.fix)
        self.setText(0, label)
        self.setText(1, min)
        self.setText(2, max)
        self.setText(3, fix)
        self.setTextAlignment(1, QtCore.Qt.AlignCenter)
        self.setTextAlignment(2, QtCore.Qt.AlignCenter)
        self.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.setFlags(QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsEditable)
        for child in node.child_node_iter():
            TreeWidgetNodeConstraints(self, child)
        self.setExpanded(True)

    def showWarning(self, message):
        QtWidgets.QMessageBox.warning(None, 'Warning',
            message, QtWidgets.QMessageBox.Ok)

    def showException(self, message):
        print(message)
        QtWidgets.QMessageBox.critical(None, 'Error',
            message, QtWidgets.QMessageBox.Ok)

    def checkConstraints(self):
        if self.node.fix is not None:
            if self.node.min is not None or self.node.max is not None:
                self.showWarning('Min/Max constraints are ignored if node is Fixed.')
        if (self.node.min is not None and
            self.node.max is not None and
            self.node.min > self.node.max):
            self.showWarning('Impossible constraints: Min > Max.')

    def editFloat(self, value):
        if value == '' or value == '-':
            return (None, '-')
        value = float(value)
        label = str(int(value)) if value.is_integer() else str(value)
        return (value, label)

    def setNodeMin(self, value):
        (self.node.min, label) = self.editFloat(value)
        self.checkConstraints()
        return label

    def setNodeMax(self, value):
        (self.node.max, label) = self.editFloat(value)
        self.checkConstraints()
        return label

    def setNodeFix(self, value):
        (self.node.fix, label) = self.editFloat(value)
        self.checkConstraints()
        return label

    def setNodeLabel(self, value):
        indexString = self.node.decorator.format(self.node.index)
        if value == '' or value == indexString:
            self.node.label = ''
            return indexString
        if re.match('^[^,;()\[\]\r\n]*$', value) is None:
            raise ValueError('Label contains invalid characters.')
        self.node.label = value
        return value

    def setData(self, column, role, value):
        try:
            if role == QtCore.Qt.ItemDataRole.EditRole:
                if column == 0:
                    value = self.setNodeLabel(value)
                elif column == 1:
                    value = self.setNodeMin(value)
                elif column == 2:
                    value = self.setNodeMax(value)
                elif column == 3:
                    value = self.setNodeFix(value)
        except Exception as exception:
            self.showException('Error: ' + str(exception))
        else:
            super().setData(column, role, value)
