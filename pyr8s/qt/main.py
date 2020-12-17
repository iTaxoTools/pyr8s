#! /usr/bin/env python
# -*- coding: utf-8 -*-

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui

import sys
import logging
import re

from .. import core
from .. import parse
from ..param import qt as param_qt

from . import utility
from . import widgets
from . import icons


class Main(QtWidgets.QDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        logger = logging.getLogger()
        # sys.stderr.write = logger.error
        # sys.stdout.write = logger.info

        self.analysis = core.RateAnalysis()

        self.setWindowTitle("pyr8s")
        self.resize(854,480)
        self.machine = None
        self.draw()
        self.stateInit()

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    @property
    def state(self):
        """Get current machine state"""
        if self.machine is not None:
            state = list(self.machine.configuration())
            return state[0].objectName()
        return None

    def reject(self):
        """Called on dialog close or <ESC>"""
        if self.state == 'STATE_RUNNING':
            self.actionCancel()
            return
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Are you sure you want to quit?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Yes)
        confirm = msgBox.exec()
        if confirm == QtWidgets.QMessageBox.Yes:
            super().reject()

    def closeMessages(self):
        """Rejects any open QMessageBoxes"""
        for widget in self.children():
            if widget.__class__ == QtWidgets.QMessageBox:
                widget.reject()

    def fail(self, exception):
        # raise exception
        self.closeMessages()
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Critical)
        msgBox.setText('An exception has occured:')
        msgBox.setInformativeText(str(exception))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
        logger = logging.getLogger()
        logger.error(str(exception))

    def stateInit(self):
        """Initialize state machine"""
        self.machine = QtCore.QStateMachine(self)

        idle = QtCore.QState()
        running = QtCore.QState()

        idle.setObjectName('STATE_IDLE')
        idle.assignProperty(self.cancelButton, 'visible', False)
        idle.assignProperty(self.runButton, 'visible', True)
        idle.assignProperty(self.paramWidget.container, 'enabled', True)
        idle.assignProperty(self.searchWidget, 'enabled', True)
        def onIdleEntry(event):
            print('IDLE', event.type())
            # self.tabResultsWidget.setCurrentIndex(0)
            self.constraintsWidget.setItemsDisabled(False)
            self.resultsWidget.setItemsDisabled(False)
            self.constraintsWidget.setFocus()
        idle.onEntry = onIdleEntry

        running.setObjectName('STATE_RUNNING')
        running.assignProperty(self.runButton, 'visible', False)
        running.assignProperty(self.cancelButton, 'visible', True)
        running.assignProperty(self.paramWidget.container, 'enabled', False)
        running.assignProperty(self.searchWidget, 'enabled', False)
        def onRunningEntry(event):
            print('RUN', event.type())
            self.tabResultsWidget.setCurrentIndex(3)
            self.constraintsWidget.setItemsDisabled(True)
            self.resultsWidget.setItemsDisabled(True)
            self.cancelButton.setFocus(True)
        running.onEntry = onRunningEntry

        transition = utility.NamedTransition('RUN')
        transition.setTargetState(running)
        idle.addTransition(transition)

        transition = utility.NamedTransition('DONE')
        def onTransitionDone(event):
            self.closeMessages()
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle(self.windowTitle())
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Analysis performed successfully.')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgBox.exec()
        transition.onTransition = onTransitionDone
        transition.setTargetState(idle)
        running.addTransition(transition)

        transition = utility.NamedTransition('FAIL')
        def onTransitionFail(event):
            self.fail(event.args[0])
        transition.onTransition = onTransitionFail
        transition.setTargetState(idle)
        running.addTransition(transition)

        transition = utility.NamedTransition('CANCEL')
        transition.setTargetState(idle)
        running.addTransition(transition)

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
        self.rightPane, self.barButtons  = self.createPaneResults()
        self.barButtons.sync(self.barLabel)

        self.leftPane.setDisabled(True)
        self.barLabel.setDisabled(False)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.leftPane)
        splitter.addWidget(self.rightPane)
        splitter.setStretchFactor(0,0)
        splitter.setStretchFactor(1,1)
        splitter.setCollapsible(0,False)
        splitter.setCollapsible(1,False)
        splitter.setStyleSheet("QSplitter::handle { height: 8px; }")
        self.splitter = splitter

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createTabConstraints(self):
        tab = QtWidgets.QWidget()

        self.constraintsWidget = widgets.TreeWidgetPhylogenetic()
        self.constraintsWidget.onSelect = (lambda data:
            self.resultsWidget.searchSelect(data[0],
                flag=QtCore.Qt.MatchExactly))
        self.constraintsWidget.setColumnCount(4)
        self.constraintsWidget.setAlternatingRowColors(True)
        self.constraintsWidget.setHeaderLabels(['Taxon', 'Min', 'Max', 'Fix'])
        headerItem = self.constraintsWidget.headerItem()
        headerItem.setTextAlignment(0, QtCore.Qt.AlignLeft)
        headerItem.setTextAlignment(1, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(2, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(3, QtCore.Qt.AlignCenter)
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
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        labelLayout = QtWidgets.QHBoxLayout()
        labelLayout.addWidget(label, 1)
        labelLayout.setContentsMargins(1, 1, 1, 1)
        labelWidget = QtWidgets.QWidget()
        labelWidget.setLayout(labelLayout)
        self.labelTree = label

        toolbar = widgets.UToolBar('Tools')
        toolbar.addWidget(labelWidget)

        tabWidget = QtWidgets.QTabWidget()

        def search(what):
            self.constraintsWidget.searchSelect(what)
            self.resultsWidget.searchSelect(what)
        self.searchWidget = widgets.TabWidgetSearch()
        self.searchWidget.setSearchAction(':/icons/search.png', search)

        def onTabChange():
            isRunning = self.state == 'STATE_RUNNING'
            if not isRunning and tabWidget.currentIndex() == 0:
                self.searchWidget.setEnabled(True)
            else:
                self.searchWidget.setEnabled(False)

        tabWidget.currentChanged.connect(onTabChange)

        tabWidget.setCornerWidget(self.searchWidget)

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

    def createTabResults(self):
        tab = QtWidgets.QWidget()

        self.resultsWidget = widgets.TreeWidgetPhylogenetic()
        self.resultsWidget.onSelect = (lambda data:
            self.constraintsWidget.searchSelect(data[0],
            flag=QtCore.Qt.MatchExactly))
        self.resultsWidget.setColumnCount(3)
        self.resultsWidget.setAlternatingRowColors(True)
        self.resultsWidget.setHeaderLabels(['Taxon', 'Age', 'Rate', 'C'])
        headerItem = self.resultsWidget.headerItem()
        headerItem.setTextAlignment(0, QtCore.Qt.AlignLeft)
        headerItem.setTextAlignment(1, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(2, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.resultsWidget.installEventFilter(self)
        self.resultsWidget.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.resultsWidget)
        tab.setLayout(layout)

        return tab

    def createTabTable(self):
        tab = QtWidgets.QWidget()

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.addWidget(paramWidget)
        tab.setLayout(layout)

        return tab

    def createTabLogs(self):
        tab = QtWidgets.QWidget()

        logWidget = utility.TextEditLogger()
        fixedFont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        logWidget.setFont(fixedFont)
        # logWidget.handler.setFormatter(
        #     logging.Formatter(
        #         '%(asctime)s %(levelname)s %(module)s %(funcName)s %(message)s'))
        logging.getLogger().addHandler(logWidget.handler)
        logging.getLogger().setLevel(logging.DEBUG)
        for i in range(100):
            logging.debug('damn, a bug')

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(logWidget)
        layout.setContentsMargins(5, 5, 5, 5)
        tab.setLayout(layout)

        return tab

    def createPaneResults(self):
        pane = QtWidgets.QWidget()

        label = QtWidgets.QLabel("Results")
        label.setAlignment(QtCore.Qt.AlignCenter)
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        labelLayout = QtWidgets.QHBoxLayout()
        labelLayout.addWidget(label, 1)
        labelLayout.setContentsMargins(1, 1, 1, 1)
        labelWidget = QtWidgets.QWidget()
        labelWidget.setLayout(labelLayout)

        exitAct = QtWidgets.QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(QtWidgets.qApp.quit)

        actionOpen = QtWidgets.QAction('Open', self)
        actionOpen.setShortcut('Ctrl+O')
        actionOpen.setStatusTip('Open an existing file')
        actionOpen.triggered.connect(self.actionOpen)

        toolbar = widgets.UToolBar('Tools')
        toolbar.addAction(actionOpen)
        toolbar.addAction('Save', lambda: self.barButtons.setMinimumHeight(68))
        # toolbar.addAction('Export', find)
        toolbar.addAction(exitAct)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        #toolbar.setStyleSheet("background-color:red;")

        self.tabResultsWidget = QtWidgets.QTabWidget()

        tab1 = self.createTabResults()
        tab2 = self.createTabTable()
        tab3 = self.createTabTable()
        tab4 = self.createTabLogs()
        self.tabResultsWidget.addTab(tab1, "&Results")
        self.tabResultsWidget.addTab(tab2, "&Diagram")
        self.tabResultsWidget.addTab(tab3, "&Table")
        self.tabResultsWidget.addTab(tab4, "&Logs")

        layout = QtWidgets.QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(self.tabResultsWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def actionRunWork(self):
        self.analysis.run()
        return self.analysis.results

    def actionRun(self):

        def done(result):
            result.print()
            self.resultsWidget.clear()
            widgets.TreeWidgetNodeResults(
                self.resultsWidget, result.tree.seed_node)
            self.tabResultsWidget.setCurrentIndex(0)
            self.machine.postEvent(utility.NamedEvent('DONE'))

        def fail(exception):
            self.machine.postEvent(utility.NamedEvent('FAIL', exception))

        try:
            self.paramWidget.applyParams()
        except Exception as exception:
            self.fail(exception)
            return

        self.launcher = utility.UProcess(self.actionRunWork)
        self.launcher.done.connect(done)
        self.launcher.fail.connect(fail)
        self.launcher.setLogger(logging.getLogger())
        self.launcher.start()
        self.machine.postEvent(utility.NamedEvent('RUN'))

    def actionCancel(self):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Cancel ongoing analysis?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm = msgBox.exec()
        if confirm == QtWidgets.QMessageBox.Yes:
            print('\nAnalysis aborted by user.')
            self.launcher.quit()
            self.machine.postEvent(utility.NamedEvent('CANCEL'))

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
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setIcon(QtWidgets.QMessageBox.Critical)
            msgBox.setText('Failed to load file:')
            msgBox.setDetailedText(str(exception.filename))
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            confirm = msgBox.exec()
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
                labelText += ': ' + treeName
            self.labelTree.setText(labelText)
            self.constraintsWidget.clear()
            # self.analysis.tree.print_plot(show_internal_node_labels=True)
            widgets.TreeWidgetNodeConstraints(
                self.constraintsWidget, self.analysis.tree.seed_node)
            idealWidth = self.constraintsWidget.idealWidth()
            width = min([self.width()/3, idealWidth])
            self.splitter.setSizes([width, 1, self.width()/3])
            self.leftPane.setDisabled(False)
        except Exception as exception:
            self.fail(exception)

def show(sys):
    """Entry point"""
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    main = Main()
    main.setWindowFlags(QtCore.Qt.Window)
    main.setModal(True)
    main.show()
    if len(sys.argv) >= 2:
        main.actionOpenFile(sys.argv[1])
    sys.exit(app.exec_())
