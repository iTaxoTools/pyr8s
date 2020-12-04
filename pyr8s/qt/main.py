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

import time #! remove this

from .. import core
from .. import parse
from ..param import qt as pqt

from multiprocessing import Process, Pipe

class Thread(QThread):
    """Multithreaded function execution"""
    done = pyqtSignal(object)
    fail = pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        # self.kwargs['thread'] = self

    def run(self):
        try:
            # print('inside', QThread.currentThread())
            result = self.function(*self.args, **self.kwargs)
        except Exception as exception:
            print('>>> EXCEPT')
            self.fail.emit(exception)
        else:
            print('>>> ALL GOOD')
            self.done.emit(result)

class SyncedWidget(QWidget):
    """Sync height with other widgets"""
    syncSignal = pyqtSignal()

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

class SToolBar(QToolBar, SyncedWidget):
    syncSignal = pyqtSignal()
    pass

class Main(QDialog):

    def __init__(self, parent=None):
        super(Main, self).__init__(parent)

        self.analysis = core.RateAnalysis()

        self.setWindowTitle("pyr8s")
        self.resize(854,480)
        self.draw()

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

        toolbar = SToolBar('Tools')
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

        toolbar = SToolBar('Tools')
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

    def run(self):

        def mf(ssss, *args, **kwargs):
            ssss.paramWidget.applyParams()
            ssss.analysis.run()
            ssss.analysis.results.print()
            return ssss.analysis.results

        def pf(connection, function, *args, **kwargs):
            try:
                # raise Exception('mama mia')
                result = function(*args, **kwargs)
                connection.send('RESULT')
                connection.send(result)
            except Exception as exception:
                connection.send('EXCEPTION')
                connection.send(exception)

        (pipeIn, pipeOut) = Pipe()
        pargs = (self,)
        pkwargs = {'test':42}
        p = Process(target=pf, args=(pipeIn,mf,)+pargs, kwargs=pkwargs, name='some_proc', daemon=True)
        p.start()

        self.q = pipeOut

        def work(*args, **kwargs):
            # print('thread', QThread.currentThread())
            check = pipeOut.recv()
            if check == 'RESULT':
                result = pipeOut.recv()
                return result
            elif check == 'EXCEPTION':
                exception = pipeOut.recv()
                raise exception

            # try except EOFError
            p.join()
            # print('BROKE')

        def done(result):
            # self.results.print()
            print('IT IS DONE')
            result.print()
            QMessageBox.information(None, 'Success',
                'Analysis performed successfully.', QMessageBox.Ok)
            pass

        def fail(exception):
            print(str(exception))
            QMessageBox.critical(None, 'Exception occured',
                str(exception), QMessageBox.Ok)

        thread = Thread(work)
        thread.setObjectName('some_thread')
        thread.started.connect(lambda: print('Analysis start'))
        thread.finished.connect(lambda: print('Analysis finish'))
        thread.fail.connect(fail)
        thread.done.connect(done)
        thread.start()
        self.thread = thread

        # print('after', QThread.currentThread())

        # self.analysis.results.print()
        # def work(*args, **kwargs):
        #     print('thread', QThread.currentThread())
        #     # self.paramWidget.applyParams()
        #     # self.analysis.run()
        #     # time.sleep(5)
        #
        # def fail(event):
        #     QMessageBox.critical(self, 'Exception occured',
        #         str(event), QMessageBox.Ok)
        #
        # print('before', QThread.currentThread())
        # thread = Thread(work)
        # print('created', QThread.currentThread())
        # thread.setObjectName('analysis')
        # thread.done.connect(lambda: print('Analysis success'))
        # thread.fail.connect(fail)
        # thread.started.connect(lambda: print('Analysis start'))
        # thread.finished.connect(lambda: print('Analysis over'))
        # thread.start()
        # print('after', QThread.currentThread())

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
    main.show()
    if len(sys.argv) >= 2:
        main.open(sys.argv[1])
    sys.exit(app.exec_())
