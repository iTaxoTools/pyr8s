#! /usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import (Qt, QObject, QFileInfo, QState, QStateMachine,
        QRunnable, QThread, QThreadPool, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QSplitter, QMainWindow, QAction, qApp, QToolBar,
        QMessageBox, QFileDialog, QTreeWidget, QTreeWidgetItem, QStyle)
from PyQt5.QtGui import QIcon, QKeySequence

from .. import core
from .. import parse
from ..param import qt as pqt

from multiprocessing import Process, Pipe

from .utility import UProcess, SyncedWidget, UToolBar
from . import icons


class TreeWidgetNode(QTreeWidgetItem):
    """Linked to a dendropy tree"""
    def __init__(self, parent, node):
        """
        Creates a widget from a dendropy node and adds it to the parent.
        Recursively creates children widgets from children nodes.
        """
        super().__init__(parent)
        label = str(node.label)
        label = '[' + label + ']' if node.is_name_dummy else label
        min = '-' if node.min is None else str(node.min)
        fix = '-' if node.fix is None else str(node.fix)
        max = '-' if node.max is None else str(node.max)
        self.setText(0, label)
        self.setText(1, min)
        self.setText(2, fix)
        self.setText(3, max)
        self.setTextAlignment(1, Qt.AlignCenter)
        self.setTextAlignment(2, Qt.AlignCenter)
        self.setTextAlignment(3, Qt.AlignCenter)
        for child in node.child_node_iter():
            print(child)
            TreeWidgetNode(self, child)
        self.setExpanded(True)


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
        idle.addTransition(self.signalRun, running)
        running.onEntry = lambda event: self.runButton.setFocus(True)

        running.assignProperty(self.runButton, 'visible', False)
        running.assignProperty(self.cancelButton, 'visible', True)
        running.assignProperty(self.paramWidget.container, 'enabled', False)
        running.addTransition(self.signalIdle, idle)
        running.onEntry = lambda event: self.cancelButton.setFocus(True)

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
        toolbar.addAction('Export')
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

        self.constraintsWidget = QTreeWidget()
        self.constraintsWidget.setColumnCount(2)
        items = []
        for i in range(10):
            a = QTreeWidgetItem(None)
            a.setText(0, 'Cities')
            b = QTreeWidgetItem(a, ['asdasd',str(i)+'.b'])
            items.append(a)
        self.constraintsWidget.insertTopLevelItems(0, items)
        self.constraintsWidget.setHeaderLabels(['Taxon', 'Min', 'Fix', 'Max'])
        self.constraintsWidget.setStyleSheet(
            """
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
        layout.setContentsMargins(0, 0, 0, 0)
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

        tab1 = self.createTabConstraints()
        tab2 = self.createTabParams()
        # tab3 = self.createTabConstraints()

        tabWidget.addTab(tab1, "&Constraints")
        tabWidget.addTab(tab2, "&Params")
        # tabWidget.addTab(tab3, "&Data")

        self.runButton = QPushButton('Run')
        self.runButton.clicked.connect(self.actionRun)
        self.runButton.setAutoDefault(True)
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
            self.analysis.tree.print_plot(show_internal_node_labels=True)
            TreeWidgetNode(self.constraintsWidget, self.analysis.tree.seed_node)
            self.constraintsWidget.resizeColumnToContents(0)
            self.constraintsWidget.resizeColumnToContents(1)
            self.constraintsWidget.resizeColumnToContents(2)
            self.constraintsWidget.resizeColumnToContents(3)
            widthTree = self.constraintsWidget.viewportSizeHint().width()
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
