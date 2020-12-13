"""Custom widgets for PyQt5"""

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui  as QtGui

import re

##############################################################################
### Phylogenetic Trees

class TreeWidgetPhylogenetic(QtWidgets.QTreeWidget):
    """Styled to draw the branches of phylogenetic trees."""
    def __init__(self):
        super().__init__()
        self.solidColor = QtGui.QColor('#555555')
        self.radiusLeaf = 3
        self.radiusInternal = 5
        self.setIndentation(16)

    def setItemsDisabled(self, disable):
        topItem = self.topLevelItem(0)
        if topItem is not None:
            topItem.setDisabled(disable)

    def drawBranches(self, painter, rect, index):
        """Manually paint branches and nodes"""
        super().drawBranches(painter, rect, index)

        solidPen = QtGui.QPen(self.solidColor)
        solidPen.setWidth(2)
        painter.setBrush(self.solidColor)
        painter.setPen(solidPen)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        indent = self.indentation()
        item = self.itemFromIndex(index)
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
        segment.setLeft(rect.width() - indent)
        rect.setWidth(indent)
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
                bottom = QtCore.QPoint(center.x(), center.y()+segment.height()/2)
                bottomMid = QtCore.QPoint(center.x(), center.y()+radius)
                painter.drawLine(bottom, bottomMid)
            else:
                painter.setBrush(self.solidColor)
                painter.drawEllipse(center, 1, 1)
            if parent is None:
                return
            left = QtCore.QPoint(center.x()-segment.width()/2, center.y())
            leftMid = QtCore.QPoint(center.x()-radius, center.y())
            painter.drawLine(left, leftMid)

        # Branch towards direct parent
        segment.moveLeft(segment.left() - indent)
        if segment.left() < 0:
            return
        if hasMoreSiblings:
            center = segment.center()
            right = QtCore.QPoint(center.x()+segment.width()/2, center.y())
            painter.drawLine(center, right)
            top = QtCore.QPoint(center.x(), segment.top())
            bottom = QtCore.QPoint(center.x(), segment.bottom())
            painter.drawLine(top, bottom)
        else:
            center = segment.center()
            right = QtCore.QPoint(center.x()+segment.width()/2, center.y())
            painter.drawLine(center, right)
            top = QtCore.QPoint(center.x(), segment.top())
            painter.drawLine(top, center)

        # Branch extensions for ancestors
        segment.moveLeft(segment.left() - indent)
        item = parent
        while parent is not None:
            parent = item.parent()
            next = None
            if parent is not None:
                i = parent.indexOfChild(item)
                next = parent.child(i+1)
            hasMoreSiblings = next is not None
            if hasMoreSiblings:
                center = segment.center()
                top = QtCore.QPoint(center.x(), segment.top())
                bottom = QtCore.QPoint(center.x(), segment.bottom())
                painter.drawLine(top, bottom)
            segment.moveLeft(segment.left() - indent)
            item = parent


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
        label = '[' + label + ']' if node.is_name_dummy else label
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
            message, QWidgets.QtWidgets.Ok)

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
        indexString = '[' + str(self.node.index) + ']'
        if value == '' or value == indexString:
            self.node.label = str(self.node.index)
            self.node.is_name_dummy = True
            return indexString
        if re.match('^[^,;()\[\]\r\n]*$', value) is None:
            raise ValueError('Label contains invalid characters.')
        self.node.is_name_dummy = False
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


##############################################################################
### Layout

class SyncedWidget(QtWidgets.QWidget):
    """Sync height with other widgets"""
    syncSignal = QtCore.pyqtSignal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if event.size().height() != event.oldSize().height():
            self.syncSignal.emit()

    def syncHandle(self):
        other = self.sender().height()
        self.setMinimumHeight(other)

    def sync(self, widget):
        self.syncSignal.connect(widget.syncHandle)
        widget.syncSignal.connect(self.syncHandle)

class UToolBar(QtWidgets.QToolBar, SyncedWidget):
    syncSignal = QtCore.pyqtSignal()
    pass
