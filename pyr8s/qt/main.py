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

    def __init__(self, parent=None, init=None):
        super(Main, self).__init__(parent)

        logging.getLogger().setLevel(logging.DEBUG)
        self.analysis = core.RateAnalysis()

        self.setWindowTitle("pyr8s")
        self.resize(854,480)
        self.machine = None
        self.draw()
        self.stateInit()

        if init is not None:
            self.machine.started.connect(init)

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    def reject(self):
        """Called on dialog close or <ESC>"""
        if self.stateCheck('STATE_RUNNING'):
            self.handleCancel()
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
        msgBox.setText('An exception occured:')
        msgBox.setInformativeText(str(exception))
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec()
        logger = logging.getLogger()
        logger.error(str(exception))

    def stateCheck(self, name):
        """Check if given state is currently running"""
        if self.machine is not None:
            for state in list(self.machine.configuration()):
                if state.objectName() == name:
                    return True
        return False

    def _stateList(self):
        """Check if given state is currently running"""
        if self.machine is not None:
            for state in list(self.machine.configuration()):
                print(state, state.objectName())

    def stateInit(self):
        """Initialize state machine"""
        self.machine = QtCore.QStateMachine(self)

        idle = QtCore.QState()
        idle_none = QtCore.QState(idle)
        idle_open = QtCore.QState(idle)
        idle_done = QtCore.QState(idle)
        idle_last = QtCore.QHistoryState(idle)
        idle.setInitialState(idle_none)
        running = QtCore.QState()

        idle.setObjectName('STATE_IDLE')
        idle.assignProperty(self.paramWidget.container, 'enabled', True)
        idle.assignProperty(self.cancelButton, 'visible', False)
        idle.assignProperty(self.runButton, 'visible', True)
        def onEntry(event):
            self.treeConstraints.setItemsDisabled(False)
            self.treeResults.setItemsDisabled(False)
            self.treeConstraints.setFocus()
        idle.onEntry = onEntry

        idle_none.setObjectName('STATE_IDLE_NONE')
        idle_none.assignProperty(self.searchWidget, 'enabled', False)
        idle_none.assignProperty(self.tabConstraints, 'enabled', False)
        idle_none.assignProperty(self.tabParams, 'enabled', False)
        idle_none.assignProperty(self.tabResults, 'enabled', False)
        idle_none.assignProperty(self.tabDiagram, 'enabled', False)
        idle_none.assignProperty(self.tabTable, 'enabled', False)
        idle_none.assignProperty(self.runButton, 'enabled', False)
        idle_none.assignProperty(self.actionSave, 'enabled', False)
        idle_none.assignProperty(self.actionExport, 'enabled', False)

        idle_open.setObjectName('STATE_IDLE_OPEN')
        idle_open.assignProperty(self.searchWidget, 'enabled', True)
        idle_open.assignProperty(self.tabConstraints, 'enabled', True)
        idle_open.assignProperty(self.tabParams, 'enabled', True)
        idle_open.assignProperty(self.tabResults, 'enabled', False)
        idle_open.assignProperty(self.tabDiagram, 'enabled', False)
        idle_open.assignProperty(self.tabTable, 'enabled', False)
        idle_open.assignProperty(self.runButton, 'enabled', True)
        idle_open.assignProperty(self.actionSave, 'enabled', True)
        idle_open.assignProperty(self.actionExport, 'enabled', False)
        def onEntry(event):
            self.tabContainerAnalysis.setCurrentIndex(0)
        idle_open.onEntry = onEntry

        idle_done.setObjectName('STATE_IDLE_DONE')
        idle_done.assignProperty(self.searchWidget, 'enabled', True)
        idle_done.assignProperty(self.tabConstraints, 'enabled', True)
        idle_done.assignProperty(self.tabParams, 'enabled', True)
        idle_done.assignProperty(self.tabResults, 'enabled', True)
        idle_done.assignProperty(self.tabDiagram, 'enabled', True)
        idle_done.assignProperty(self.tabTable, 'enabled', True)
        idle_done.assignProperty(self.runButton, 'enabled', True)
        idle_done.assignProperty(self.actionSave, 'enabled', True)
        idle_done.assignProperty(self.actionExport, 'enabled', True)
        def onEntry(event):
            self.tabContainerAnalysis.setCurrentIndex(0)
            self.tabContainerResults.setCurrentIndex(0)
        idle_done.onEntry = onEntry

        running.setObjectName('STATE_RUNNING')
        running.assignProperty(self.runButton, 'visible', False)
        running.assignProperty(self.cancelButton, 'visible', True)
        running.assignProperty(self.paramWidget.container, 'enabled', False)
        def onEntry(event):
            self.tabContainerResults.setCurrentIndex(3)
            self.treeConstraints.setItemsDisabled(True)
            self.treeResults.setItemsDisabled(True)
            self.cancelButton.setFocus(True)
        running.onEntry = onEntry

        transition = utility.NamedTransition('OPEN')
        def onTransition(event):
            fileInfo = QtCore.QFileInfo(event.kwargs['file'])
            labelText = fileInfo.baseName()
            treeName = self.analysis.tree.label
            if len(treeName) > 0:
                labelText += ': ' + treeName
            self.labelTree.setText(labelText)
            self.treeResults.clear()
            self.treeConstraints.clear()
            widgets.TreeWidgetNodeConstraints(
                self.treeConstraints, self.analysis.tree.seed_node)
            idealWidth = self.treeConstraints.idealWidth()
            width = min([self.width()/2, idealWidth])
            self.splitter.setSizes([width, 1, self.width()/2])
        transition.onTransition = onTransition
        transition.setTargetState(idle_open)
        idle.addTransition(transition)

        transition = utility.NamedTransition('RUN')
        transition.setTargetState(running)
        idle.addTransition(transition)

        transition = utility.NamedTransition('DONE')
        def onTransition(event):
            results = event.args[0]
            self.treeResults.clear()
            widgets.TreeWidgetNodeResults(
                self.treeResults, results.tree.seed_node)
            self.closeMessages()
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle(self.windowTitle())
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Analysis performed successfully.')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            msgBox.exec()
        transition.onTransition = onTransition
        transition.setTargetState(idle_done)
        running.addTransition(transition)

        transition = utility.NamedTransition('FAIL')
        def onTransition(event):
            self.tabContainerResults.setCurrentIndex(3)
            self.fail(event.args[0])
        transition.onTransition = onTransition
        transition.setTargetState(idle_last)
        running.addTransition(transition)

        transition = utility.NamedTransition('CANCEL')
        transition.setTargetState(idle_last)
        running.addTransition(transition)

        self.machine.addState(idle)
        self.machine.addState(running)
        self.machine.setInitialState(idle)
        self.machine.start()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if (source == self.treeConstraints and
                event.key() == QtCore.Qt.Key_Return and
                self.treeConstraints.state() !=
                    QtWidgets.QAbstractItemView.EditingState):
                self.handleRun()
                return True
        return QtCore.QObject.eventFilter(self, source, event)

    def draw(self):
        """Draw all widgets"""
        self.leftPane, self.barLabel = self.createPaneEdit()
        self.rightPane, self.barButtons  = self.createPaneResults()
        self.barButtons.sync(self.barLabel)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.leftPane)
        self.splitter.addWidget(self.rightPane)
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setCollapsible(0,False)
        self.splitter.setCollapsible(1,False)
        self.splitter.setStyleSheet("QSplitter::handle { height: 8px; }")

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createTabConstraints(self):
        tab = QtWidgets.QWidget()

        self.treeConstraints = widgets.TreeWidgetPhylogenetic()
        self.treeConstraints.onSelect = (lambda data:
            self.treeResults.searchSelect(data[0],
                flag=QtCore.Qt.MatchExactly))
        self.treeConstraints.setColumnCount(4)
        self.treeConstraints.setAlternatingRowColors(True)
        self.treeConstraints.setHeaderLabels(['Taxon', 'Min', 'Max', 'Fix'])
        headerItem = self.treeConstraints.headerItem()
        headerItem.setTextAlignment(0, QtCore.Qt.AlignLeft)
        headerItem.setTextAlignment(1, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(2, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.treeConstraints.installEventFilter(self)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.treeConstraints)
        tab.setLayout(layout)

        return tab

    def createTabParams(self):
        tab = QtWidgets.QWidget()
        self.paramWidget = param_qt.ParamContainer(self.analysis.param)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.paramWidget)
        tab.setLayout(layout)

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

        self.tabContainerAnalysis = QtWidgets.QTabWidget()

        def search(what):
            self.treeConstraints.searchSelect(what)
            self.treeResults.searchSelect(what)
        self.searchWidget = widgets.TabWidgetSearch()
        self.searchWidget.setSearchAction(':/icons/search.png', search)

        self.tabContainerAnalysis.setCornerWidget(self.searchWidget)

        self.tabConstraints = self.createTabConstraints()
        self.tabParams = self.createTabParams()
        self.tabContainerAnalysis.addTab(self.tabConstraints, "&Constraints")
        self.tabContainerAnalysis.addTab(self.tabParams, "&Params")

        self.runButton = QtWidgets.QPushButton('Run')
        self.runButton.clicked.connect(self.handleRun)
        self.runButton.setAutoDefault(False)
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.handleCancel)
        self.cancelButton.setAutoDefault(True)

        runLayout = QtWidgets.QVBoxLayout()
        runLayout.addWidget(self.runButton)
        runLayout.addWidget(self.cancelButton)
        runWidget = QtWidgets.QGroupBox()
        runWidget.setLayout(runLayout)

        layout = QtWidgets.QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(self.tabContainerAnalysis)
        layout.addWidget(runWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def createTabResults(self):
        tab = QtWidgets.QWidget()

        self.treeResults = widgets.TreeWidgetPhylogenetic()
        self.treeResults.onSelect = (lambda data:
            self.treeConstraints.searchSelect(data[0],
            flag=QtCore.Qt.MatchExactly))
        self.treeResults.setColumnCount(3)
        self.treeResults.setAlternatingRowColors(True)
        self.treeResults.setHeaderLabels(['Taxon', 'Age', 'Rate', 'C'])
        headerItem = self.treeResults.headerItem()
        headerItem.setTextAlignment(0, QtCore.Qt.AlignLeft)
        headerItem.setTextAlignment(1, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(2, QtCore.Qt.AlignCenter)
        headerItem.setTextAlignment(3, QtCore.Qt.AlignCenter)
        self.treeResults.installEventFilter(self)
        self.treeResults.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.treeResults)
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

        self.actionSave = QtWidgets.QAction('&Save', self)
        self.actionSave.setShortcut('Ctrl+S')
        self.actionSave.setStatusTip('Save analysis state')
        self.actionSave.triggered.connect(self.handleSave)

        self.actionOpen = QtWidgets.QAction('&Open', self)
        self.actionOpen.setShortcut('Ctrl+O')
        self.actionOpen.setStatusTip('Open an existing file')
        self.actionOpen.triggered.connect(self.handleOpen)

        self.actionExport = QtWidgets.QAction('&Export', self)
        self.actionExport.setStatusTip('Export results')

        self.actionExportChrono = QtWidgets.QAction('&Chronogram', self)
        self.actionExportChrono.setShortcut('Ctrl+E')
        self.actionExportChrono.setStatusTip('Export chronogram (ultrametric)')
        self.actionExportChrono.triggered.connect(self.handleExportChrono)

        self.actionExportRato = QtWidgets.QAction('&Ratogram', self)
        self.actionExportRato.setStatusTip('Export ratogram')
        self.actionExportRato.triggered.connect(self.handleExportRato)

        self.actionExportTable = QtWidgets.QAction('&Table', self)
        self.actionExportTable.setStatusTip('Export ages and rates table')
        self.actionExportTable.triggered.connect(self.handleExportTable)

        exportButton = QtWidgets.QToolButton(self)
        exportButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        exportMenu = QtWidgets.QMenu(exportButton)
        exportMenu.addAction(self.actionExportChrono)
        exportMenu.addAction(self.actionExportRato)
        exportMenu.addAction(self.actionExportTable)
        exportButton.setDefaultAction(self.actionExport)
        exportButton.setMenu(exportMenu)

        toolbar = widgets.UToolBar('Tools')
        toolbar.addAction(self.actionOpen)
        toolbar.addAction(self.actionSave)
        toolbar.addWidget(exportButton)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        #toolbar.setStyleSheet("background-color:red;")

        self.tabContainerResults = QtWidgets.QTabWidget()

        self.tabResults = self.createTabResults()
        self.tabDiagram = self.createTabTable()
        self.tabTable = self.createTabTable()
        self.tabLogs = self.createTabLogs()
        self.tabContainerResults.addTab(self.tabResults, "&Results")
        self.tabContainerResults.addTab(self.tabDiagram , "&Diagram")
        self.tabContainerResults.addTab(self.tabTable, "&Table")
        self.tabContainerResults.addTab(self.tabLogs, "&Logs")

        layout = QtWidgets.QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(self.tabContainerResults)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def handleRunWork(self):
        """Runs on the UProcess, defined here for pickability"""
        self.analysis.run()
        return self.analysis.results

    def handleRun(self):
        """Called by Run button"""
        try:
            self.paramWidget.applyParams()
        except Exception as exception:
            self.fail(exception)
            return

        def done(result):
            with utility.StdioLogger():
                result.print()
                print(result.chronogram.as_string(schema='newick'))
            self.analysis.results = result
            self.machine.postEvent(utility.NamedEvent('DONE', result))

        def fail(exception):
            self.machine.postEvent(utility.NamedEvent('FAIL', exception))

        self.launcher = utility.UProcess(self.handleRunWork)
        self.launcher.done.connect(done)
        self.launcher.fail.connect(fail)
        self.launcher.setLogger(logging.getLogger())
        self.launcher.start()
        self.machine.postEvent(utility.NamedEvent('RUN'))

    def handleCancel(self):
        """Called by cancel button"""
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Cancel ongoing analysis?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm = msgBox.exec()
        if confirm == QtWidgets.QMessageBox.Yes:
            logging.getLogger().info('\nAnalysis aborted by user.')
            self.launcher.quit()
            self.machine.postEvent(utility.NamedEvent('CANCEL'))

    def handleOpen(self):
        """Called by toolbar action"""
        (fileName, _) = QtWidgets.QFileDialog.getOpenFileName(self, 'pyr8s - Open File')
        if len(fileName) > 0:
            self.handleOpenFile(fileName)

    def handleSave(self):
        """Called by toolbar button"""
        self.barButtons.setMinimumHeight(68)
        pass

    def handleExportChrono(self):
        """Called by toolbar menu button"""
        (fileName, filter) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Chronogram',
            QtCore.QDir.homePath() + '/' + self.analysis.tree.label + '.nwk',
            'Newick (*.nwk);;  All files (*.*)')
        if len(fileName) == 0:
            return
        try:
            with open(fileName, 'w') as file:
                file.write(self.analysis.results.chronogram.
                    as_string(schema='newick'))
        except Exception as exception:
            self.fail(exception)
        finally:
            logging.getLogger().info(
                'Exported chronogram to file: {}\n'.format(fileName))

    def handleExportRato(self):
        """Called by toolbar menu button"""
        (fileName, filter) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Chronogram',
            QtCore.QDir.homePath() + '/' + self.analysis.tree.label + '.nwk',
            'Newick (*.nwk);;  All files (*.*)')
        if len(fileName) == 0:
            return
        try:
            with open(fileName, 'w') as file:
                file.write(self.analysis.results.ratogram.
                    as_string(schema='newick'))
        except Exception as exception:
            self.fail(exception)
        finally:
            logging.getLogger().info(
                'Exported chronogram to file: {}\n'.format(fileName))

    def handleExportTable(self):
        """Called by toolbar menu button"""
        (fileName, filter) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Chronogram',
            QtCore.QDir.homePath() + '/' + self.analysis.tree.label + '.tsv',
            'Tab Separated Values (*.tsv);;  All files (*.*)')
        if len(fileName) == 0:
            return
        try:
            with open(fileName, 'w') as file:
                table = self.analysis.results.table
                for i in range(table['n']):
                    file.write(str(table['Node'][i]) + '\t')
                    file.write(str(table['Age'][i]) + '\t')
                    file.write(str(table['Rate'][i]) + '\n')
        except Exception as exception:
            self.fail(exception)
        finally:
            logging.getLogger().info(
                'Exported chronogram to file: {}\n'.format(fileName))

    def handleOpenFile(self, file):
        """Load tree from file"""
        try:
            with utility.StdioLogger():
                self.analysis = parse.from_file(file)
                print("Loaded file: " + file)
            self.paramWidget.setParams(self.analysis.param)
        except Exception as exception:
            self.fail(exception)
        else:
            self.machine.postEvent(utility.NamedEvent('OPEN',file=file))

def show(sys):
    """Entry point"""
    def init():
        if len(sys.argv) >= 2:
            main.handleOpenFile(sys.argv[1])

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    main = Main(init=init)
    main.setWindowFlags(QtCore.Qt.Window)
    main.setModal(True)
    main.show()
    sys.exit(app.exec_())
