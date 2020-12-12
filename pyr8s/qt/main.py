#! /usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import (Qt, QObject, QFileInfo, QState, QStateMachine, QRect,
        QSize, QRunnable, QThread, QThreadPool, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QTabBar,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QSplitter, QMainWindow, QAction, qApp, QToolBar,
        QMessageBox, QFileDialog, QTreeWidget, QTreeWidgetItem, QStyle, QHeaderView)
from PyQt5.QtGui import (QGuiApplication, QPalette, QIcon, QPixmap,
        QColor, QBrush, QKeySequence)

import re

from .. import core
from .. import parse
from ..param import qt as pqt

from multiprocessing import Process, Pipe

from .utility import UProcess, SyncedWidget, UToolBar
from . import icons

class QTreeWidgetCustom(QTreeWidget):
    def drawBranches(self, painter, rect, index):
        # print('>>>',rect)

        super().drawBranches(painter, rect, index)

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

        # color = QColor('yellow')
        # if hasChildren:
        #     color = QColor('green')
        # elif hasMoreSiblings:
        #     color = QColor('red')

        # Node view for self first
        segment = QRect(rect)
        segment.setLeft(rect.width() - indent)
        rect.setWidth(indent)
        if not hasChildren:
            color = QColor('blue')
            brush = QBrush(color)
            painter.fillRect(segment, brush)
        else:
            if isExpanded:
                color = QColor('green')
                brush = QBrush(color)
                painter.fillRect(segment, brush)
            else:
                color = QColor('red')
                brush = QBrush(color)
                painter.fillRect(segment, brush)

        # Branch view from direct parent
        segment.setLeft(segment.left() - indent)
        segment.setWidth(indent)
        if segment.left() < 0:
            return
        if hasMoreSiblings:
            color = QColor('cyan')
            brush = QBrush(color)
            painter.fillRect(segment, brush)
        else:
            color = QColor('magenta')
            brush = QBrush(color)
            painter.fillRect(segment, brush)

        # Branch extensions for ancestors
        segment.setLeft(segment.left() - indent)
        segment.setWidth(indent)
        item = parent
        while parent is not None:
            parent = item.parent()
            next = None
            if parent is not None:
                i = parent.indexOfChild(item)
                next = parent.child(i+1)
            hasMoreSiblings = next is not None
            if hasMoreSiblings:
                color = QColor('yellow')
                brush = QBrush(color)
                painter.fillRect(segment, brush)
            segment.setLeft(segment.left() - indent)
            segment.setWidth(indent)
            item = parent


        color = self.palette().color(QPalette.Shadow)
        # if isExpanded:
        #     color = self.palette().color(QPalette.Mid)

        brush = QBrush()
        brush.setColor(color)
        brush.setStyle(Qt.SolidPattern)

        # rect.setLeft(rect.width() - 2*indent)
        # rect.setWidth(indent)
        # painter.fillRect(rect, brush)

        # opt = self.viewOptions()
        # opt.rect = rect
        # opt.state = QStyle.State_Item | QStyle.State_Sibling
        # self.style().drawPrimitive(QStyle.PE_IndicatorBranch, opt, painter, self)

class TreeWidgetNode(QTreeWidgetItem):
    """Linked to a dendropy tree"""
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
        self.setTextAlignment(1, Qt.AlignCenter)
        self.setTextAlignment(2, Qt.AlignCenter)
        self.setTextAlignment(3, Qt.AlignCenter)
        self.setFlags(Qt.ItemIsSelectable |
                      Qt.ItemIsEnabled |
                      Qt.ItemIsEditable)
        # self.setIcon(0, QIcon(":/icons/search.png"))
        for child in node.child_node_iter():
            # print(child)
            TreeWidgetNode(self, child)
        self.setExpanded(True)

    def editFloat(self, value):
        if value == '' or value == '-':
            return (None, '-')
        value = float(value)
        label = str(int(value)) if value.is_integer() else str(value)
        return (value, label)

    def showWarning(self, message):
        QMessageBox.warning(None, 'Warning',
            message, QMessageBox.Ok)

    def showException(self, message):
        print(message)
        QMessageBox.critical(None, 'Error',
            message, QMessageBox.Ok)

    def checkConstraints(self):
        if self.node.fix is not None:
            if self.node.min is not None or self.node.max is not None:
                self.showWarning('Min/Max constraints are ignored if node is Fixed.')
        if (self.node.min is not None and
            self.node.max is not None and
            self.node.min > self.node.max):
            self.showWarning('Impossible constraints: Min > Max.')

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

    def setData(self, column, role, value):
        # print('DATA',self, column, role, value)
        # if role == Qt.ItemDataRole.DisplayRole or \
        try:
            if role == Qt.ItemDataRole.EditRole:
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


class Main(QDialog):
    """Main window, handles everything"""

    signalRun = pyqtSignal()
    signalIdle = pyqtSignal()

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        self.analysis = core.RateAnalysis()

        self.setWindowTitle("pyr8s")
        self.resize(854,480)
        self.draw()
        self.state()

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    def fail(self, exception):
        print(str(exception))
        QMessageBox.critical(None, 'Exception occured',
            str(exception), QMessageBox.Ok)

    def state(self):
        self.machine = QStateMachine(self)

        idle = QState()
        running = QState()

        idle.assignProperty(self.cancelButton, 'visible', False)
        idle.assignProperty(self.runButton, 'visible', True)
        idle.assignProperty(self.paramWidget.container, 'enabled', True)
        idle.assignProperty(self.constraintsWidget, 'enabled', True)
        idle.assignProperty(self.findWidget, 'enabled', True)
        idle.addTransition(self.signalRun, running)
        def onIdleEntry(event):
            self.runButton.setFocus(True)
        idle.onEntry = onIdleEntry

        running.assignProperty(self.runButton, 'visible', False)
        running.assignProperty(self.cancelButton, 'visible', True)
        running.assignProperty(self.paramWidget.container, 'enabled', False)
        running.assignProperty(self.constraintsWidget, 'enabled', False)
        running.assignProperty(self.findWidget, 'enabled', False)
        running.addTransition(self.signalIdle, idle)
        def onRunningEntry(event):
            self.cancelButton.setFocus(True)
        idle.onEntry = onRunningEntry

        self.machine.addState(idle)
        self.machine.addState(running)
        self.machine.setInitialState(idle)
        self.machine.start()


    def draw(self):
        """Draw all widgets"""
        self.leftPane, self.barLabel = self.createPaneEdit()
        self.rightPane, self.barButton  = self.createPaneCanvas()
        self.barButton.sync(self.barLabel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.leftPane)
        splitter.addWidget(self.rightPane)
        splitter.setStretchFactor(0,0)
        splitter.setStretchFactor(1,1)
        splitter.setCollapsible(0,False)
        self.splitter = splitter

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createPaneCanvas(self):
        pane = QWidget()

        exitAct = QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qApp.quit)

        actionOpen = QAction('Open', self)
        actionOpen.setShortcut('Ctrl+O')
        actionOpen.setStatusTip('Open an existing file')
        actionOpen.triggered.connect(self.actionOpen)

        toolbar = UToolBar('Tools')
        toolbar.addAction(actionOpen)
        toolbar.addAction('Save', lambda: self.barButton.setMinimumHeight(68))
        # toolbar.addAction('Export', find)
        toolbar.addAction(exitAct)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        #toolbar.setStyleSheet("background-color:red;")

        canvas = QGroupBox()
        canvas.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def createTabConstraints(self):
        tab = QWidget()


        def onDoubleClick(item, index):
            self.constraintsWidget.editItem(item, index)

        # def onItemChanged(item, column):
        #     print('CHANGE', self.analysis.param.general.scalar )

        self.constraintsWidget = QTreeWidgetCustom()
        self.constraintsWidget.itemActivated.connect(onDoubleClick)
        # self.constraintsWidget.itemChanged.connect(onItemChanged)
        self.constraintsWidget.setColumnCount(4)
        self.constraintsWidget.setAlternatingRowColors(True)
        self.constraintsWidget.setHeaderLabels(['Taxon', 'Min', 'Max', 'Fix'])
        header = self.constraintsWidget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        headerItem = self.constraintsWidget.headerItem()
        headerItem.setTextAlignment(0, Qt.AlignLeft)
        headerItem.setTextAlignment(1, Qt.AlignCenter)
        headerItem.setTextAlignment(2, Qt.AlignCenter)
        headerItem.setTextAlignment(3, Qt.AlignCenter)
        # self.constraintsWidget.setIndentation(8)
        self.constraintsWidget.setUniformRowHeights(True)
        self.constraintsWidget.setStyleSheet(
            """
            QTreeView {
                show-decoration-selected: 1;
            }

            QTreeView::item {
                 border: 1px solid #d9d9d9;
                border-top-color: transparent;
                border-bottom-color: transparent;
            }

            QTreeView::item:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
                border: 1px solid #bfcde4;
            }

            QTreeView::item:selected {
                border: 1px solid #567dbc;
            }

            QTreeView::item:selected:active{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);
            }
            QTreeView::branch {
                    background: palette(base);
            }

            QTreeView::branch:has-siblings:!adjoins-item {
                    background: cyan;
            }

            QTreeView::branch:has-siblings:adjoins-item {
                    background: red;
            }

            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                    background: blue;
            }

            QTreeView::branch:closed:has-children:has-siblings {
                    background: pink;
            }

            QTreeView::branch:has-children:!has-siblings:closed {
                    background: gray;
            }

            QTreeView::branch:open:has-children:has-siblings {
                    background: magenta;
            }

            QTreeView::branch:open:has-children:!has-siblings {
                    background: green;
            }
            QTreeView::item:selected:!active {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6b9be8, stop: 1 #577fbf);
            }
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: url(:/icons/vline.png) 0;
            }
            QTreeView::branch:has-siblings:adjoins-item {
                border-image: url(:/icons/branch-more.png) 0;
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: url(:/icons/branch-end.png) 0;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                    border-image: none;
                    image: url(:/icons/branch-closed.png);
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings  {
                    border-image: none;
                    image: url(:/icons/branch-open.png);
            }
            """
            )
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.constraintsWidget)
        tab.setLayout(layout)

        return tab

    def createTabParams(self):
        tab = QWidget()
        paramWidget = pqt.ParamContainer(self.analysis.param)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(paramWidget)
        tab.setLayout(layout)

        self.paramWidget = paramWidget
        return tab

    def createPaneEdit(self):
        pane = QWidget()

        label = QLabel("Tree of Life")
        label.setAlignment(Qt.AlignCenter)
        #label.setStyleSheet("background-color:green;")
        labelLayout = QHBoxLayout()
        labelLayout.addWidget(label, 1)
        labelLayout.setContentsMargins(1, 1, 1, 1)
        labelWidget = QWidget()
        labelWidget.setLayout(labelLayout)
        self.labelTree = label

        toolbar = UToolBar('Tools')
        toolbar.addWidget(labelWidget)
        #toolbar.setStyleSheet("background-color:red;")

        tabWidget = QTabWidget()

        findEdit = QLineEdit()
        label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        findEdit.setStyleSheet(
        """
        QLineEdit {
            border: none;
            background: transparent;
            padding: 0 4px;
        }
        """)

        def find():
            what = findEdit.text()
            if what == '':
                return
            self.constraintsWidget.clearSelection()
            found = self.constraintsWidget.findItems(what, Qt.MatchContains | Qt.MatchRecursive)
            for item in found:
                item.setSelected(True)
                self.constraintsWidget.scrollToItem(item)

        pixmap = QPixmap(':/icons/search.png')
        mask = pixmap.createMaskFromColor(QColor('black'), Qt.MaskOutColor)
        palette = QGuiApplication.palette()
        pixmap.fill(palette.color(QPalette.Shadow))
        pixmap.setMask(mask)

        findAction = QAction(QIcon(pixmap), 'Search', self)
        findAction.triggered.connect(find)
        findEdit.addAction(findAction, QLineEdit.TrailingPosition)

        # btn.setStyleSheet("QLineEdit { border: none; background: transparent }")
        findWidget = QGroupBox()
        findLayout = QHBoxLayout()
        findLayout.addWidget(findEdit)
        findLayout.setContentsMargins(0, 0, 0, 0)
        findWidget.setLayout(findLayout)
        findWidget.setStyleSheet(
            # background: palette(Light);
        """
        QGroupBox {
            border: 1px solid palette(dark);
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            min-width: 1ex;
            padding: 2px;
            margin: 0px;
            width: 150px;
        }
        QGroupBox:enabled  {
            background: palette(Light);
        }
        QGroupBox:!enabled  {
            background: palette(Window);
        }
        """)
        self.findWidget = findWidget

        def onTabChange():
            if tabWidget.currentIndex() == 0:
                findWidget.setEnabled(True)
            else:
                findWidget.setEnabled(False)

        tabWidget.currentChanged.connect(onTabChange)

        tabWidget.setCornerWidget(findWidget)

        tab1 = self.createTabConstraints()
        tab2 = self.createTabParams()
        tabWidget.addTab(tab1, "&Constraints")
        tabWidget.addTab(tab2, "&Params")

        self.runButton = QPushButton('Run')
        self.runButton.clicked.connect(self.actionRun)
        self.runButton.setAutoDefault(False)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.actionCancel)
        self.cancelButton.setAutoDefault(True)

        runLayout = QVBoxLayout()
        runLayout.addWidget(self.runButton)
        runLayout.addWidget(self.cancelButton)
        runWidget = QGroupBox()
        runWidget.setLayout(runLayout)

        layout = QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(tabWidget)
        layout.addWidget(runWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def actionRunWork(self):
        self.analysis.run()
        return self.analysis.results

    def actionRun(self):

        def done(result):
            result.print()
            QMessageBox.information(None, 'Success',
                'Analysis performed successfully.', QMessageBox.Ok)
            self.signalIdle.emit()

        def fail(exception):
            self.fail(exception)
            self.signalIdle.emit()

        try:
            self.paramWidget.applyParams()
        except Exception as exception:
            self.fail(exception)
            return

        self.launcher = UProcess(self.actionRunWork)
        self.launcher.started.connect(self.signalRun.emit)
        # self.launcher.finished.connect()
        self.launcher.done.connect(done)
        self.launcher.fail.connect(fail)
        self.launcher.start()

    def actionCancel(self):
        print('Analysis aborted by user.')
        self.launcher.quit()
        self.signalIdle.emit()

    def actionOpen(self):
        (fileName, _) = QFileDialog.getOpenFileName(self, 'Open File')
        if len(fileName) > 0:
            self.actionOpenFile(fileName)

    def actionOpenFile(self, file):
        """Load tree from file"""
        try:
            self.analysis = parse.from_file(file)
            print("Loaded file: " + file)
        except FileNotFoundError as exception:
            QMessageBox.critical(self, 'Exception occured',
                "Failed to load file: " + exception.filename, QMessageBox.Ok)
        except Exception as exception:
            self.fail(exception)
        else:
            self.actionOpenUpdate(file)

    def actionOpenUpdate(self, file):
        try:
            self.paramWidget.setParams(self.analysis.param)
            fileInfo = QFileInfo(file)
            labelText = fileInfo.baseName()
            treeName = self.analysis.tree.label
            if len(treeName) > 0:
                labelText += '/' + treeName
            self.labelTree.setText(labelText)
            self.constraintsWidget.clear()
            # self.analysis.tree.print_plot(show_internal_node_labels=True)
            TreeWidgetNode(self.constraintsWidget, self.analysis.tree.seed_node)

            header = self.constraintsWidget.header()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            widthTree = self.constraintsWidget.viewportSizeHint().width()
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            widthScrollbar = qApp.style().pixelMetric(QStyle.PM_ScrollBarExtent)
            widthPadding = 10
            self.splitter.setSizes([widthTree+widthScrollbar+widthPadding, 1])
        except Exception as exception:
            self.fail(exception)


def show(sys):
    """Entry point"""
    app = QApplication(sys.argv)
    main = Main()
    main.setWindowFlags(Qt.Window)
    main.show()
    if len(sys.argv) >= 2:
        main.actionOpenFile(sys.argv[1])
    sys.exit(app.exec_())
