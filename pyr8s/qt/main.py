#! /usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import (Qt, QObject, QRunnable, QThread, QThreadPool,
        pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QSplitter, QMainWindow, QAction, qApp, QToolBar,
        QMessageBox)
from PyQt5.QtGui import QIcon

from .. import core
from .. import parse
from ..param import qt as pqt

from multiprocessing import Process, Pipe

from .utility import UProcess, SyncedWidget, UToolBar

class Main(QDialog):
    """Main window, handles everything"""
    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        self.analysis = core.RateAnalysis()

        self.setWindowTitle("pyr8s")
        self.resize(854,480)
        self.draw()

    def __getstate__(self):
        return (self.analysis,)

    def __setstate__(self, state):
        (self.analysis,) = state

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

        layout = QHBoxLayout(self)
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def createPaneCanvas(self):
        pane = QWidget()

        exitAct = QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qApp.quit)

        toolbar = UToolBar('Tools')
        toolbar.addAction('Open', lambda: print('GO FISH'))
        toolbar.addAction('Save', lambda: self.barButton.setMinimumHeight(68))
        toolbar.addAction('Export')
        toolbar.addAction(exitAct)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setStyleSheet("background-color:red;")

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
        tableWidget = QTableWidget(10, 10)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tableWidget)
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
        label.setStyleSheet("background-color:green;")
        labelLayout = QHBoxLayout()
        labelLayout.addWidget(label, 1)
        labelLayout.setContentsMargins(1, 1, 1, 1)
        labelWidget = QWidget()
        labelWidget.setLayout(labelLayout)

        toolbar = UToolBar('Tools')
        toolbar.addWidget(labelWidget)
        toolbar.setStyleSheet("background-color:red;")

        tabWidget = QTabWidget()

        tab1 = self.createTabParams()
        tab2 = self.createTabConstraints()
        tab3 = self.createTabConstraints()

        tabWidget.addTab(tab1, "&Contraints")
        tabWidget.addTab(tab2, "&Data")
        tabWidget.addTab(tab3, "&Params")

        runButton = QPushButton('Run')
        runButton.clicked.connect(self.run)
        runLayout = QVBoxLayout()
        runLayout.addWidget(runButton)
        runWidget = QGroupBox()
        runWidget.setLayout(runLayout)

        layout = QVBoxLayout()
        layout.setMenuBar(toolbar)
        layout.addWidget(tabWidget)
        layout.addWidget(runWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        pane.setLayout(layout)

        return pane, toolbar

    def run_work(self):
        self.analysis.run()
        return self.analysis.results

    def run(self):

        def done(result):
            result.print()
            QMessageBox.information(None, 'Success',
                'Analysis performed successfully.', QMessageBox.Ok)
            pass

        def fail(exception):
            print(str(exception))
            QMessageBox.critical(None, 'Exception occured',
                str(exception), QMessageBox.Ok)

        try:
            self.paramWidget.applyParams()
        except Exception as exception:
            fail(exception)

        self.launcher = UProcess(self.run_work)
        self.launcher.started.connect(lambda: print('Analysis start'))
        self.launcher.finished.connect(lambda: print('Analysis finish'))
        self.launcher.done.connect(done)
        self.launcher.fail.connect(fail)
        self.launcher.start()

    def open(self, file):
        """Load tree from file"""
        try:
            self.analysis.tree_from_file(file)
            print("Loaded file: " + file)
        except FileNotFoundError as e:
            QMessageBox.critical(self, 'Exception occured',
                "Failed to load file: " + e.filename, QMessageBox.Ok)


def show(sys):
    """Entry point"""
    app = QApplication(sys.argv)
    main = Main()
    main.setWindowFlags(Qt.Window)
    main.show()
    if len(sys.argv) >= 2:
        main.open(sys.argv[1])
    sys.exit(app.exec_())
