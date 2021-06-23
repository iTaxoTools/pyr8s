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


from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtStateMachine
from PySide6 import QtGui

import sys
import re
import pickle
import pathlib
import importlib.resources

from itaxotools.common.param import qt as param_qt
from itaxotools.common import utility
from itaxotools.common import widgets
from itaxotools import resources

from .. import core
from .. import parse

from . import trees


_resource_path = importlib.resources.files(resources)
def get_resource(path):
    return str(_resource_path / path)
def get_icon(path):
    return str(_resource_path / 'icons/svg' / path)


class Main(widgets.ToolDialog):
    """Main window, handles everything"""

    def __init__(self, parent=None, init=None):
        super(Main, self).__init__(parent)

        self.title = 'ASAPy'
        self.analysis = core.RateAnalysis()

        self.setWindowTitle(self.title)
        self.setWindowIcon(QtGui.QIcon(get_resource('icons/ico/pyr8s.ico')))
        self.resize(854,480)

        self.process = None
        self.machine = None
        self.skin()
        self.draw()
        self.act()
        self.cog()

        if init is not None:
            self.machine.started.connect(init)


    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

    def onReject(self):
        """If running, verify cancel"""
        if self.state['running'] in list(self.machine.configuration()):
            self.handleStop()
            return True
        else:
            return None

    def cog(self):
        """Initialize state machine"""

        self.state = {}
        self.state['idle'] = QtStateMachine.QState()
        self.state['idle_none'] = QtStateMachine.QState(self.state['idle'])
        self.state['idle_open'] = QtStateMachine.QState(self.state['idle'])
        self.state['idle_done'] = QtStateMachine.QState(self.state['idle'])
        self.state['done_complete'] = QtStateMachine.QState(self.state['idle_done'])
        self.state['done_updated'] = QtStateMachine.QState(self.state['idle_done'])
        self.state['idle_last'] = QtStateMachine.QHistoryState(self.state['idle'])
        self.state['running'] = QtStateMachine.QState()
        self.state['idle'].setInitialState(self.state['idle_none'])
        self.state['idle_done'].setInitialState(self.state['done_complete'])

        state = self.state['idle']
        state.assignProperty(self.action['run'], 'visible', True)
        state.assignProperty(self.action['stop'], 'visible', False)
        state.assignProperty(self.action['open'], 'enabled', True)
        def onEntry(event):
            self.treeConstraints.setItemsDisabled(False)
            self.treeResults.setItemsDisabled(False)
            self.setFocus()
        state.onEntry = onEntry

        state = self.state['idle_none']
        state.assignProperty(self.action['run'], 'enabled', False)
        state.assignProperty(self.action['save'], 'enabled', False)
        state.assignProperty(self.action['export'], 'enabled', False)
        state.assignProperty(self.tab['constraints'], 'enabled', False)
        state.assignProperty(self.tab['results'], 'enabled', False)
        state.assignProperty(self.paramWidget.container, 'enabled', False)
        state.assignProperty(self.searchWidget, 'enabled', True)
        state.assignProperty(self.barFlags, 'enabled', False)
        state.assignProperty(self.labelFlagInfo, 'text', 'Nothing to show')
        state.assignProperty(self.labelFlagInfo, 'visible', True)
        state.assignProperty(self.labelFlagWarn, 'visible', False)

        state = self.state['idle_open']
        state.assignProperty(self.action['run'], 'enabled', True)
        state.assignProperty(self.action['save'], 'enabled', True)
        state.assignProperty(self.action['export'], 'enabled', False)
        state.assignProperty(self.tab['constraints'], 'enabled', True)
        state.assignProperty(self.tab['results'], 'enabled', False)
        state.assignProperty(self.paramWidget.container, 'enabled', True)
        state.assignProperty(self.searchWidget, 'enabled', True)
        state.assignProperty(self.barFlags, 'enabled', True)
        state.assignProperty(self.labelFlagInfo, 'text', 'Ready to run rate analysis.')
        state.assignProperty(self.labelFlagInfo, 'visible', True)
        state.assignProperty(self.labelFlagWarn, 'visible', False)
        def onEntry(event):
            self.pane['analysis'].setCurrentIndex(0)
            self.setFocus()
        state.onEntry = onEntry

        state = self.state['idle_done']
        state.assignProperty(self.action['run'], 'enabled', True)
        state.assignProperty(self.action['save'], 'enabled', True)
        state.assignProperty(self.action['export'], 'enabled', True)
        state.assignProperty(self.tab['constraints'], 'enabled', True)
        state.assignProperty(self.tab['results'], 'enabled', True)
        state.assignProperty(self.paramWidget.container, 'enabled', True)
        state.assignProperty(self.searchWidget, 'enabled', True)

        state = self.state['running']
        state.assignProperty(self.action['run'], 'visible', False)
        state.assignProperty(self.action['stop'], 'visible', True)
        state.assignProperty(self.action['open'], 'enabled', False)
        state.assignProperty(self.action['save'], 'enabled', False)
        state.assignProperty(self.action['export'], 'enabled', False)
        state.assignProperty(self.paramWidget.container, 'enabled', False)
        state.assignProperty(self.searchWidget, 'enabled', False)
        state.assignProperty(self.barFlags, 'enabled', True)
        state.assignProperty(self.labelFlagInfo, 'text', 'Please wait...')
        state.assignProperty(self.labelFlagWarn, 'visible', False)
        def onEntry(event):
            self.pane['results'].setCurrentIndex(1)
            self.treeConstraints.setItemsDisabled(True)
            self.treeResults.setItemsDisabled(True)
        state.onEntry = onEntry

        state = self.state['done_complete']
        state.assignProperty(self.barFlags, 'enabled', True)
        state.assignProperty(self.labelFlagInfo, 'text', 'Analysis complete.')
        state.assignProperty(self.labelFlagInfo, 'visible', False)
        state.assignProperty(self.labelFlagWarn, 'visible', True)
        def onEntry(event):
            self.pane['analysis'].setCurrentIndex(0)
            self.pane['results'].setCurrentIndex(0)
        state.onEntry = onEntry

        state = self.state['done_updated']
        state.assignProperty(self.barFlags, 'enabled', True)
        state.assignProperty(self.labelFlagInfo, 'visible', False)
        state.assignProperty(self.labelFlagWarn, 'visible', True)
        state.assignProperty(self.labelFlagWarn, 'text',
            'Parameters have changed, re-run analysis to update results.')

        transition = utility.NamedTransition('OPEN')
        def onTransition(event):
            fileInfo = QtCore.QFileInfo(event.kwargs['file'])
            labelText = fileInfo.baseName()
            self.setWindowTitle(self.title + ' - ' + labelText)
            treeName = self.analysis.tree.label
            if treeName is not None:
                if len(treeName) > 0 and treeName != labelText:
                    labelText += ': ' + treeName
            self.labelTree.setText(labelText)
            self.treeResults.clear()
            self.treeConstraints.clear()
            trees.TreeWidgetNodeConstraints(
                self.treeConstraints, self.analysis.tree.seed_node)
            idealWidth = self.treeConstraints.idealWidth()
            width = min([self.width()/2, idealWidth])
            self.splitter.setSizes([width, 1, self.width()/2])
            if self.analysis.results is not None:
                self.machine.postEvent(utility.NamedEvent('LOAD'))
        transition.onTransition = onTransition
        transition.setTargetState(self.state['idle_open'])
        self.state['idle'].addTransition(transition)

        transition = utility.NamedTransition('LOAD')
        def onTransition(event):
            warning = self.analysis.results.flags['warning']
            self.labelFlagWarn.setText(warning)
            self.treeResults.clear()
            trees.TreeWidgetNodeResults(
                self.treeResults, self.analysis.results.tree.seed_node)
        transition.onTransition = onTransition
        transition.setTargetState(self.state['idle_done'])
        self.state['idle'].addTransition(transition)

        transition = utility.NamedTransition('RUN')
        transition.setTargetState(self.state['running'])
        self.state['idle'].addTransition(transition)

        transition = utility.NamedTransition('DONE')
        def onTransition(event):
            warning = self.analysis.results.flags['warning']
            self.labelFlagWarn.setText(warning)
            self.treeResults.clear()
            trees.TreeWidgetNodeResults(
                self.treeResults, self.analysis.results.tree.seed_node)
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle(self.windowTitle())
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Analysis complete.')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            self.msgShow(msgBox)
        transition.onTransition = onTransition
        transition.setTargetState(self.state['done_complete'])
        self.state['running'].addTransition(transition)

        transition = utility.NamedTransition('UPDATE')
        transition.setTargetState(self.state['done_updated'])
        self.state['idle_done'].addTransition(transition)

        transition = utility.NamedTransition('FAIL')
        def onTransition(event):
            self.pane['results'].setCurrentIndex(1)
            self.fail(event.args[0])
        transition.onTransition = onTransition
        transition.setTargetState(self.state['idle_last'])
        self.state['running'].addTransition(transition)

        transition = utility.NamedTransition('CANCEL')
        transition.setTargetState(self.state['idle_last'])
        self.state['running'].addTransition(transition)

        self.machine = QtStateMachine.QStateMachine(self)
        self.machine.addState(self.state['idle'])
        self.machine.addState(self.state['running'])
        self.machine.setInitialState(self.state['idle'])
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

    def skin(self):
        """Configure widget appearance"""
        color = {
            'white':  '#ffffff',
            'light':  '#eff1ee',
            'beige':  '#e1e0de',
            'gray':   '#abaaa8',
            'iron':   '#8b8d8a',
            'black':  '#454241',
            'red':    '#ee4e5f',
            'pink':   '#eb9597',
            'orange': '#eb6a4a',
            'brown':  '#655c5d',
            'green':  '#00ff00',
            }
        # using green for debugging
        palette = QtGui.QGuiApplication.palette()
        scheme = {
            QtGui.QPalette.Active: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'black',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'brown',
                QtGui.QPalette.Text: 'black',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'black',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'red',
                QtGui.QPalette.HighlightedText: 'white',
                # These work on linux only?
                QtGui.QPalette.ToolTipBase: 'beige',
                QtGui.QPalette.ToolTipText: 'brown',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.Link: 'green',
                QtGui.QPalette.LinkVisited: 'green',
                },
            QtGui.QPalette.Disabled: {
                QtGui.QPalette.Window: 'light',
                QtGui.QPalette.WindowText: 'iron',
                QtGui.QPalette.Base: 'white',
                QtGui.QPalette.AlternateBase: 'light',
                QtGui.QPalette.PlaceholderText: 'green',
                QtGui.QPalette.Text: 'iron',
                QtGui.QPalette.Button: 'light',
                QtGui.QPalette.ButtonText: 'gray',
                QtGui.QPalette.Light: 'white',
                QtGui.QPalette.Midlight: 'beige',
                QtGui.QPalette.Mid: 'gray',
                QtGui.QPalette.Dark: 'iron',
                QtGui.QPalette.Shadow: 'brown',
                QtGui.QPalette.Highlight: 'pink',
                QtGui.QPalette.HighlightedText: 'white',
                # These seem bugged anyway
                QtGui.QPalette.BrightText: 'green',
                QtGui.QPalette.ToolTipBase: 'green',
                QtGui.QPalette.ToolTipText: 'green',
                QtGui.QPalette.Link: 'green',
                QtGui.QPalette.LinkVisited: 'green',
                },
            }
        scheme[QtGui.QPalette.Inactive] = scheme[QtGui.QPalette.Active]
        for group in scheme:
            for role in scheme[group]:
                palette.setColor(group, role,
                    QtGui.QColor(color[scheme[group][role]]))
        QtGui.QGuiApplication.setPalette(palette)

        self.colormap = {
            widgets.VectorIcon.Normal: {
                '#000': color['black'],
                '#f00': color['red'],
                },
            widgets.VectorIcon.Disabled: {
                '#000': color['gray'],
                '#f00': color['orange'],
                },
            }
        self.colormap_icon =  {
            '#000': color['black'],
            '#ff0000': color['red'],
            '#ffa500': color['pink'],
            }
        self.colormap_icon_light =  {
            '#000': color['iron'],
            '#ff0000': color['red'],
            '#ffa500': color['pink'],
            }
        self.colormap_graph =  {
            'abgd': {
                'black':   color['black'],
                '#D82424': color['red'],
                '#EBE448': color['gray'],
                },
            'disthist': {
                'black':   color['black'],
                '#EBE448': color['beige'],
                },
            'rank': {
                'black':   color['black'],
                '#D82424': color['red'],
                },
            }

    def draw(self):
        """Draw all widgets"""

        self.header = widgets.Header()
        self.header.logoTool = widgets.VectorPixmap(get_resource('logos/svg/pyr8s.svg'),
            colormap=self.colormap_icon)
        self.header.logoProject = QtGui.QPixmap(get_resource('logos/png/itaxotools-micrologo.png'))
        self.header.description = (
            'Pyr8s - Computing timetrees' + '\n'
            'using non-parametric rate-smoothing'
            )
        self.header.citation = (
            'Pyr8s by Stefanos Patmanidis' + '\n'
            'Based on r8s by Mike Sanderson'
        )

        self.line = widgets.Subheader()

        self.line.icon = QtWidgets.QLabel()
        self.line.icon.setPixmap(widgets.VectorPixmap(get_icon('arrow-right.svg'),
            colormap=self.colormap_icon_light))
        self.line.icon.setStyleSheet('border-style: none;')

        self.labelTree = QtWidgets.QLabel("Open a file to begin")
        self.labelTree.setStyleSheet("""
            QLabel {
                color: palette(Shadow);
                font-size: 14px;
                letter-spacing: 1px;
                padding: 2px 4px 2px 4px;
                border: none;
                }
            """)
        self.labelTree.setAlignment(QtCore.Qt.AlignCenter)
        self.labelTree.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)

        def search(what):
            self.treeConstraints.searchSelect(what)
            self.treeResults.searchSelect(what)
        self.searchWidget = widgets.SearchWidget()
        pixmap = widgets.VectorPixmap(get_icon('search.svg'),
            colormap=self.colormap_icon_light)
        self.searchWidget.setSearchAction(pixmap, search)
        layout = QtWidgets.QHBoxLayout()
        layout.addSpacing(4)
        layout.addWidget(self.line.icon)
        layout.addSpacing(2)
        layout.addWidget(self.labelTree)
        layout.addSpacing(14)
        layout.addStretch(1)
        layout.addWidget(self.searchWidget)
        layout.addSpacing(8)
        layout.setContentsMargins(4, 4, 4, 4)
        self.line.setLayout(layout)

        self.pane = {}
        self.tab = {}
        self.leftPane = self.createPaneEdit()
        self.rightPane  = self.createPaneResults()

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.leftPane)
        self.splitter.addWidget(self.rightPane)
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setCollapsible(0,False)
        self.splitter.setCollapsible(1,False)
        self.splitter.setStyleSheet("QSplitter::handle { height: 8px; }")
        self.splitter.setContentsMargins(8, 4, 8, 4)

        layoutFlags = QtWidgets.QHBoxLayout()
        layoutFlags.addWidget(self.labelFlagInfo)
        layoutFlags.addWidget(self.labelFlagWarn)
        self.barFlags = QtWidgets.QGroupBox()
        self.barFlags.setObjectName('barFlags')
        self.barFlags.setLayout(layoutFlags)
        self.barFlags.setStyleSheet("""
            QGroupBox {
                color: palette(Shadow);
                background: palette(Window);
                border-top: 1px solid palette(Mid);
                padding: 5px 10px 5px 10px;
                }
            QGroupBox:disabled {
                color: palette(Mid);
                background: palette(Window);
                border-top: 1px solid palette(Mid);
                }
            """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.header, 0)
        layout.addWidget(self.line, 0)
        layout.addSpacing(8)
        layout.addWidget(self.splitter, 1)
        layout.addSpacing(8)
        layout.addWidget(self.barFlags, 0)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def act(self):
        """Populate dialog actions"""
        self.action = {}

        self.action['open'] = QtGui.QAction('&Open', self)
        self.action['open'].setIcon(widgets.VectorIcon(get_icon('open.svg'), self.colormap))
        self.action['open'].setShortcut(QtGui.QKeySequence.Open)
        self.action['open'].setStatusTip('Open an existing file')
        self.action['open'].triggered.connect(self.handleOpen)

        self.action['save'] = QtGui.QAction('&Save', self)
        self.action['save'].setIcon(widgets.VectorIcon(get_icon('save.svg'), self.colormap))
        self.action['save'].setShortcut(QtGui.QKeySequence.Save)
        self.action['save'].setStatusTip('Save analysis state')
        self.action['save'].triggered.connect(self.handleSaveAnalysis)

        self.action['run'] = QtGui.QAction('&Run', self)
        self.action['run'].setIcon(widgets.VectorIcon(get_icon('run.svg'), self.colormap))
        self.action['run'].setShortcut('Ctrl+R')
        self.action['run'].setStatusTip('Run rate analysis')
        self.action['run'].triggered.connect(self.handleRun)

        self.action['stop'] = QtGui.QAction('&Stop', self)
        self.action['stop'].setIcon(widgets.VectorIcon(get_icon('stop.svg'), self.colormap))
        self.action['stop'].setStatusTip('Cancel analysis')
        self.action['stop'].triggered.connect(self.handleStop)

        self.action['export'] = QtGui.QAction('&Export', self)
        self.action['export'].setIcon(widgets.VectorIcon(get_icon('export.svg'), self.colormap))
        self.action['export'].setStatusTip('Export results')

        self.action['export_chrono'] = QtGui.QAction('&Chronogram', self)
        self.action['export_chrono'].setShortcut('Ctrl+E')
        self.action['export_chrono'].setStatusTip('Export chronogram (ultrametric)')
        self.action['export_chrono'].triggered.connect(self.handleExportChrono)

        self.action['export_rato'] = QtGui.QAction('&Ratogram', self)
        self.action['export_rato'].setStatusTip('Export ratogram')
        self.action['export_rato'].triggered.connect(self.handleExportRato)

        self.action['export_table'] = QtGui.QAction('&Table', self)
        self.action['export_table'].setStatusTip('Export ages and rates table')
        self.action['export_table'].triggered.connect(self.handleExportTable)

        exportButton = QtWidgets.QToolButton(self)
        exportButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        exportButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        exportMenu = QtWidgets.QMenu(exportButton)
        exportMenu.addAction(self.action['export_chrono'])
        exportMenu.addAction(self.action['export_rato'])
        exportMenu.addAction(self.action['export_table'])
        exportButton.setDefaultAction(self.action['export'])
        exportButton.setMenu(exportMenu)

        self.header.toolbar.addAction(self.action['open'])
        self.header.toolbar.addAction(self.action['save'])
        self.header.toolbar.addWidget(exportButton)
        self.header.toolbar.addAction(self.action['run'])
        self.header.toolbar.addAction(self.action['stop'])

    def createTabConstraints(self):
        tab = QtWidgets.QWidget()

        self.treeConstraints = trees.TreeWidgetPhylogenetic()
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

        #! BUGGED, should be fixed and restored
        # self.treeConstraints.itemChanged.connect(
            # lambda i, c: self.machine.postEvent(utility.NamedEvent('UPDATE')))

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.treeConstraints)
        tab.setLayout(layout)

        return tab

    def createTabParams(self):
        tab = QtWidgets.QWidget()
        self.paramWidget = param_qt.ParamContainer(self.analysis.param)
        self.paramWidget.paramChanged.connect(
            lambda e: self.machine.postEvent(utility.NamedEvent('UPDATE')))

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.paramWidget)
        tab.setLayout(layout)

        return tab

    def createPaneEdit(self):
        pane = QtWidgets.QWidget()

        self.pane['analysis'] = QtWidgets.QTabWidget()

        self.tab['constraints'] = self.createTabConstraints()
        self.tab['results'] = self.createTabParams()
        self.pane['analysis'].addTab(self.tab['constraints'], "&Constraints")
        self.pane['analysis'].addTab(self.tab['results'], "&Parameters")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.pane['analysis'])
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane

    def createTabResults(self):
        tab = QtWidgets.QWidget()

        self.treeResults = trees.TreeWidgetPhylogenetic()
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

        self.logw = utility.TextEditLogger()
        fixedFont = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self.logw.setFont(fixedFont)
        self.logio = utility.TextEditLoggerIO(self.logw)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.logw)
        layout.setContentsMargins(5, 5, 5, 5)
        tab.setLayout(layout)

        return tab

    def createPaneResults(self):
        pane = QtWidgets.QWidget()

        self.pane['results'] = QtWidgets.QTabWidget()

        self.tabResults = self.createTabResults()
        self.tabDiagram = self.createTabTable()
        self.tabTable = self.createTabTable()
        self.tabLogs = self.createTabLogs()
        self.pane['results'].addTab(self.tabResults, "&Results")
        # self.pane['results'].addTab(self.tabDiagram , "&Diagram")
        # self.pane['results'].addTab(self.tabTable, "&Table")
        self.pane['results'].addTab(self.tabLogs, "&Logs")

        self.labelFlagInfo = QtWidgets.QLabel('No results to display.')
        self.labelFlagInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.labelFlagWarn = QtWidgets.QLabel('All seems good.')
        self.labelFlagWarn.setAlignment(QtCore.Qt.AlignCenter)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.pane['results'])
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane

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

        if self.analysis.param.general.scalar:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setWindowTitle(self.windowTitle())
            msgBox.setIcon(QtWidgets.QMessageBox.Question)
            msgBox.setText('Scalar mode activated, all time constraints will be ignored.')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.Ok)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
            confirm = self.msgShow(msgBox)
            if confirm == QtWidgets.QMessageBox.Cancel:
                return

        def done(result):
            with utility.redirect(sys, 'stdout', self.logio):
                result.print()
                print(result.chronogram.as_string(schema='newick'))
            self.analysis.results = result
            self.machine.postEvent(utility.NamedEvent('DONE', True))

        def fail(exception):
            self.machine.postEvent(utility.NamedEvent('FAIL', exception))

        self.process = utility.UProcess(self.handleRunWork)
        self.process.done.connect(done)
        self.process.fail.connect(fail)
        self.process.setStream(self.logio)
        self.process.start()
        self.machine.postEvent(utility.NamedEvent('RUN'))

    def handleStop(self):
        """Called by cancel button"""
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setWindowTitle(self.windowTitle())
        msgBox.setIcon(QtWidgets.QMessageBox.Question)
        msgBox.setText('Cancel ongoing analysis?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
        confirm = self.msgShow(msgBox)
        if confirm == QtWidgets.QMessageBox.Yes:
            self.logio.writeline('\nAnalysis aborted by user.')
            if self.process is not None:
                self.process.quit()
            self.machine.postEvent(utility.NamedEvent('CANCEL'))

    def handleOpen(self):
        """Called by toolbar action"""
        (fileName, _) = QtWidgets.QFileDialog.getOpenFileName(self,
            'pyr8s - Open File',
            QtCore.QDir.currentPath(),
            'All Files (*) ;; Newick (*.nwk) ;; Rates Analysis (*.r8s)')
        if len(fileName) == 0:
            return
        suffix = QtCore.QFileInfo(fileName).suffix()
        if suffix == 'r8s':
            self.handleOpenAnalysis(fileName)
        else:
            self.handleOpenFile(fileName)

    def handleOpenAnalysis(self, fileName):
        """Open pickled analysis"""
        #! THIS IS UNSAFE: Only open trusted files
        try:
            with open(fileName, 'rb') as file:
                obj = pickle.load(file)
                if obj.__class__ != core.RateAnalysis:
                    raise ValueError('Not a valid Analysis file.')
                self.analysis = obj
                self.paramWidget.setParams(self.analysis.param)
                self.machine.postEvent(utility.NamedEvent('OPEN',file=fileName))
        except Exception as exception:
            self.fail(exception)
        else:
            self.logio.writeline(
                'Loaded analysis from: {}\n'.format(fileName))

    def handleOpenFile(self, fileName):
        """Load tree from a newick or nexus file"""
        try:
            with utility.redirect(sys, 'stdout', self.logio):
                self.analysis = parse.from_file(fileName)
            self.paramWidget.setParams(self.analysis.param)
        except Exception as exception:
            self.fail(exception)
        else:
            self.logio.writeline(
                'Loaded tree from: {}\n'.format(fileName))
            self.machine.postEvent(utility.NamedEvent('OPEN',file=fileName))

    def handleSaveAnalysis(self):
        """Pickle and save current analysis"""
        (fileName, _) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Save Analysis',
            QtCore.QDir.currentPath() + '/' + self.analysis.tree.label + '.r8s',
            'Rates Analysis (*.r8s)')
        if len(fileName) == 0:
            return
        try:
            self.paramWidget.applyParams()
            with open(fileName, 'wb') as file:
                pickle.dump(self.analysis, file)
        except Exception as exception:
            self.fail(exception)
        else:
            self.logio.writeline(
                'Saved analysis to file: {}\n'.format(fileName))
        pass

    def handleExportChrono(self):
        """Called by toolbar menu button"""
        (fileName, _) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Chronogram',
            QtCore.QDir.currentPath() + '/' + self.analysis.tree.label + '_chronogram.nwk',
            'Newick (*.nwk);;  All files (*.*)')
        if len(fileName) == 0:
            return
        try:
            with open(fileName, 'w') as file:
                file.write(self.analysis.results.chronogram.
                    as_string(schema='newick'))
        except Exception as exception:
            self.fail(exception)
        else:
            self.logio.writeline(
                'Exported chronogram to file: {}\n'.format(fileName))

    def handleExportRato(self):
        """Called by toolbar menu button"""
        (fileName, _) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Ratogram',
            QtCore.QDir.currentPath() + '/' + self.analysis.tree.label + '_ratogram.nwk',
            'Newick (*.nwk);;  All files (*.*)')
        if len(fileName) == 0:
            return
        try:
            with open(fileName, 'w') as file:
                file.write(self.analysis.results.ratogram.
                    as_string(schema='newick'))
        except Exception as exception:
            self.fail(exception)
        else:
            self.logio.writeline(
                'Exported ratogram to file: {}\n'.format(fileName))

    def handleExportTable(self):
        """Called by toolbar menu button"""
        (fileName, _) = QtWidgets.QFileDialog.getSaveFileName(self,
            'pyr8s - Export Table',
            QtCore.QDir.currentPath() + '/' + self.analysis.tree.label + '_rates.tsv',
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
        else:
            self.logio.writeline(
                'Exported table to file: {}\n'.format(fileName))

def show():
    """Entry point"""
    def init():
        if len(sys.argv) >= 2:
            file = pathlib.Path(sys.argv[1])
            if file.suffix == '.r8s':
                main.handleOpenAnalysis(str(file))
            else:
                main.handleOpenFile(str(file))

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    main = Main(init=init)
    main.setWindowFlags(QtCore.Qt.Window)
    main.setModal(True)
    main.show()
    sys.exit(app.exec_())
