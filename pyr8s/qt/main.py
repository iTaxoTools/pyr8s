#! /usr/bin/env python
# -*- coding: utf-8 -*-

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui

import re

from .. import core
from .. import parse
from ..param import qt as param_qt

from . import utility
from . import widgets
from . import icons


class Main(QtWidgets.QDialog):
    """Main window, handles everything"""

    signalRun = QtCore.pyqtSignal()
    signalIdle = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        self.analysis = core.RateAnalysis()

        self.setWindowTitle("pyr8s")
        self.resize(854,480)
        self.machine = None
        self.draw()
        self.state()

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    def fail(self, exception):
        print(str(exception))
        QtWidgets.QMessageBox.critical(None, 'Exception occured',
            str(exception), QtWidgets.QMessageBox.Ok)

    def state(self):
        self.machine = QtCore.QStateMachine(self)

        idle = QtCore.QState()
        running = QtCore.QState()

        idle.setObjectName('STATE_IDLE')
        running.setObjectName('STATE_RUNNING')

        idle.assignProperty(self.cancelButton, 'visible', False)
        idle.assignProperty(self.runButton, 'visible', True)
        idle.assignProperty(self.paramWidget.container, 'enabled', True)
        idle.assignProperty(self.findWidget, 'enabled', True)
        idle.addTransition(self.signalRun, running)
        def onIdleEntry(event):
            self.constraintsWidget.setItemsDisabled(False)
            self.constraintsWidget.setFocus()
        idle.onEntry = onIdleEntry

        running.assignProperty(self.runButton, 'visible', False)
        running.assignProperty(self.cancelButton, 'visible', True)
        running.assignProperty(self.paramWidget.container, 'enabled', False)
        running.assignProperty(self.findWidget, 'enabled', False)
        running.addTransition(self.signalIdle, idle)
        def onRunningEntry(event):
            self.constraintsWidget.setItemsDisabled(True)
            self.cancelButton.setFocus(True)
        running.onEntry = onRunningEntry

        self.machine.addState(idle)
        self.machine.addState(running)
        self.machine.setInitialState(idle)
        self.machine.start()


    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if (source == self.constraintsWidget and
                event.key() == QtCore.Qt.Key_Return and
                self.constraintsWidget.state() !=
                    QtWidgets.QAbstractItemView.EditingState):
                self.actionRun()
                return True
        return QtCore.QObject.eventFilter(self, source, event)

    def draw(self):
        """Draw all widgets"""
        self.leftPane, self.barLabel = self.createPaneEdit()
        self.rightPane, self.barButton  = self.createPaneCanvas()
        self.barButton.sync(self.barLabel)

        self.leftPane.setDisabled(True)
        self.barLabel.setDisabled(False)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.leftPane)
        splitter.addWidget(self.rightPane)
        splitter.setStretchFactor(0,0)
        splitter.setStretchFactor(1,1)
        splitter.setCollapsible(0,False)
        self.splitter = splitter

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createPaneCanvas(self):
        pane = QtWidgets.QWidget()

        exitAct = QtWidgets.QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(QtWidgets.qApp.quit)

        actionOpen = QtWidgets.QAction('Open', self)
        actionOpen.setShortcut('Ctrl+O')
        actionOpen.setStatusTip('Open an existing file')
        actionOpen.triggered.connect(self.actionOpen)

        toolbar = widgets.UToolBar('Tools')
        toolbar.addAction(actionOpen)
        toolbar.addAction('Save', lambda: self.barButton.setMinimumHeight(68))
        # toolbar.addAction('Export', find)
        toolbar.addAction(exitAct)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        #toolbar.setStyleSheet("background-color:red;")

        canvas = QtWidgets.QGroupBox()
        canvas.setContentsMargins(0, 0, 0, 0)

        layout = QtWidgets.QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def createTabConstraints(self):
        tab = QtWidgets.QWidget()

        def onDoubleClick(item, index):
            self.constraintsWidget.editItem(item, index)

        # def onItemChanged(item, column):
        #     print('CHANGE', self.analysis.param.general.scalar )

        self.constraintsWidget = widgets.TreeWidgetPhylogenetic()
        self.constraintsWidget.itemActivated.connect(onDoubleClick)
        # self.constraintsWidget.itemChanged.connect(onItemChanged)
        self.constraintsWidget.setColumnCount(4)
        self.constraintsWidget.setAlternatingRowColors(True)
        self.constraintsWidget.setHeaderLabels(['Taxon', 'Min', 'Max', 'Fix'])
        header = self.constraintsWidget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        headerItem = self.constraintsWidget.headerItem()
        headerItem.setTextAlignment(0, QtCore.Qt.AlignLeft)
        headerItem.setTextAlignment(1, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(2, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.constraintsWidget.setUniformRowHeights(True)
        self.constraintsWidget.setStyleSheet(
            """
            QTreeView::branch:has-siblings:!adjoins-item {
                border-image: none;
            }
            QTreeView::branch:has-siblings:adjoins-item {
                border-image: none;
            }
            QTreeView::branch:!has-children:!has-siblings:adjoins-item {
                border-image: none;
            }
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {
                    border-image: none;
                    image: none;
            }
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings  {
                    border-image: none;
                    image: none;
            }
            """
            )
        self.constraintsWidget.installEventFilter(self)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.constraintsWidget)
        tab.setLayout(layout)

        return tab

    def createTabParams(self):
        tab = QtWidgets.QWidget()
        paramWidget = param_qt.ParamContainer(self.analysis.param)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(paramWidget)
        tab.setLayout(layout)

        self.paramWidget = paramWidget
        return tab

    def createPaneEdit(self):
        pane = QtWidgets.QWidget()

        label = QtWidgets.QLabel("Time & Rate Divergence Analysis")
        label.setAlignment(QtCore.Qt.AlignCenter)
        #label.setStyleSheet("background-color:green;")
        labelLayout = QtWidgets.QHBoxLayout()
        labelLayout.addWidget(label, 1)
        labelLayout.setContentsMargins(1, 1, 1, 1)
        labelWidget = QtWidgets.QWidget()
        labelWidget.setLayout(labelLayout)
        self.labelTree = label

        toolbar = widgets.UToolBar('Tools')
        toolbar.addWidget(labelWidget)
        #toolbar.setStyleSheet("background-color:red;")

        tabWidget = QtWidgets.QTabWidget()

        findEdit = QtWidgets.QLineEdit()
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
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
                self.constraintsWidget.clearSelection()
                return
            self.constraintsWidget.clearSelection()
            found = self.constraintsWidget.findItems(what, QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive)
            for item in found:
                item.setSelected(True)
                self.constraintsWidget.scrollToItem(item)

        pixmap = QtGui.QPixmap(':/icons/search.png')
        mask = pixmap.createMaskFromColor(QtGui.QColor('black'), QtCore.Qt.MaskOutColor)
        palette = QtGui.QGuiApplication.palette()
        pixmap.fill(palette.color(QtGui.QPalette.Shadow))
        pixmap.setMask(mask)

        findAction = QtWidgets.QAction(QtGui.QIcon(pixmap), 'Search', self)
        findAction.triggered.connect(find)
        findEdit.addAction(findAction, QtWidgets.QLineEdit.TrailingPosition)
        findEdit.returnPressed.connect(find)
        # btn.setStyleSheet("QLineEdit { border: none; background: transparent }")
        findWidget = QtWidgets.QGroupBox()
        findLayout = QtWidgets.QHBoxLayout()
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
            isRunning = False
            if self.machine is not None:
                state = list(self.machine.configuration())
                if state[0].objectName() == 'STATE_RUNNING':
                    isRunning = True
            if not isRunning and tabWidget.currentIndex() == 0:
                findWidget.setEnabled(True)
            else:
                findWidget.setEnabled(False)

        tabWidget.currentChanged.connect(onTabChange)

        tabWidget.setCornerWidget(findWidget)

        tab1 = self.createTabConstraints()
        tab2 = self.createTabParams()
        tabWidget.addTab(tab1, "&Constraints")
        tabWidget.addTab(tab2, "&Params")

        self.runButton = QtWidgets.QPushButton('Run')
        self.runButton.clicked.connect(self.actionRun)
        self.runButton.setAutoDefault(False)
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.actionCancel)
        self.cancelButton.setAutoDefault(True)

        runLayout = QtWidgets.QVBoxLayout()
        runLayout.addWidget(self.runButton)
        runLayout.addWidget(self.cancelButton)
        runWidget = QtWidgets.QGroupBox()
        runWidget.setLayout(runLayout)

        layout = QtWidgets.QVBoxLayout()
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
            QtWidgets.QMessageBox.information(None, 'Success',
                'Analysis performed successfully.', QtWidgets.QMessageBox.Ok)
            self.signalIdle.emit()

        def fail(exception):
            self.fail(exception)
            self.signalIdle.emit()

        try:
            self.paramWidget.applyParams()
        except Exception as exception:
            self.fail(exception)
            return

        self.launcher = utility.UProcess(self.actionRunWork)
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
        (fileName, _) = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File')
        if len(fileName) > 0:
            self.actionOpenFile(fileName)

    def actionOpenFile(self, file):
        """Load tree from file"""
        try:
            self.analysis = parse.from_file(file)
            print("Loaded file: " + file)
        except FileNotFoundError as exception:
            QtWidgets.QMessageBox.critical(self, 'Exception occured',
                "Failed to load file: " + exception.filename, QtWidgets.QMessageBox.Ok)
        except Exception as exception:
            self.fail(exception)
        else:
            self.actionOpenUpdate(file)

    def actionOpenUpdate(self, file):
        try:
            self.paramWidget.setParams(self.analysis.param)
            fileInfo = QtCore.QFileInfo(file)
            labelText = fileInfo.baseName()
            treeName = self.analysis.tree.label
            if len(treeName) > 0:
                labelText += '/' + treeName
            self.labelTree.setText(labelText)
            self.constraintsWidget.clear()
            # self.analysis.tree.print_plot(show_internal_node_labels=True)
            widgets.TreeWidgetNodeConstraints(self.constraintsWidget, self.analysis.tree.seed_node)

            header = self.constraintsWidget.header()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            widthTree = self.constraintsWidget.viewportSizeHint().width()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            widthScrollbar = QtWidgets.qApp.style().pixelMetric(
                QtWidgets.QStyle.PM_ScrollBarExtent)
            widthPadding = 30
            self.splitter.setSizes([widthTree+widthScrollbar+widthPadding, 1])
            self.leftPane.setDisabled(False)
        except Exception as exception:
            self.fail(exception)


def show(sys):
    """Entry point"""
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.setWindowFlags(QtCore.Qt.Window)
    main.show()
    if len(sys.argv) >= 2:
        main.actionOpenFile(sys.argv[1])
    sys.exit(app.exec_())
