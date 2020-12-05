"""Utility functions for PyQt5"""

from PyQt5.QtCore import QRunnable, QThread, pyqtSignal, pyqtSlot # <
from PyQt5.QtWidgets import QWidget, QToolBar

from multiprocessing import Process, Pipe

##############################################################################
### Widgets

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

class UToolBar(QToolBar, SyncedWidget):
    syncSignal = pyqtSignal()
    pass


##############################################################################
### Multiprocessing

class UThread(QThread):
    """
    Multithreaded function execution using PyQt5.
    Initialise with the function and parameters for execution.
    Signals are used to communicate with parent thread.
    Use self.start() to fork/spawn.

    Signals:
    ----------
    started():
        Inherited. Emitted on start.
    finished():
        Inherited. Emitted on finish, regardless of success.
    done(result):
        Emitted when the called function returned successfully.
        Passes the result.
    fail(exception):
        Emitted if an exception occured. Passes the exception.
    """
    done = pyqtSignal(object)
    fail = pyqtSignal(object)

    def __init__(self, function, *args, **kwargs):
        """
        Parameters
        ----------
        function : function
            The function to run on the new thread.
        \*args : positional argument, optional
            If given, it is passed on to the function.
        \*\*kwargs : keyword arguments, optional
            If given, it is passed on to the function.
        """
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        # self.kwargs['thread'] = self

    def run(self):
        """
        Overloads QThread. This is run on a new thread.
        Do not call this directly, call self.start() instead.
        """
        try:
            # print('inside', QThread.currentThread())
            result = self.function(*self.args, **self.kwargs)
        except Exception as exception:
            # print('>>> EXCEPT')
            self.fail.emit(exception)
        else:
            # print('>>> ALL GOOD')
            self.done.emit(result)

class UProcess(UThread):
    """
    Multiprocess function execution using PyQt5.
    Unlike QtCore.QProcess, this launches python functions, not programs.
    Use self.start() to fork/spawn.
    """
    done = pyqtSignal(object)
    fail = pyqtSignal(object)

    def __getstate__(self):
        """
        Required for Windows process spawning.
        Nothing is saved.
        """
        return {}

    def __setstate__(self, data):
        """
        Required for Windows process spawning.
        Nothing is restored.
        """
        return

    def __init__(self, function, *args, **kwargs):
        """
        Parameters
        ----------
        function : function
            The function to run on the new process.
        *args : positional argument, optional
            If given, it is passed on to the function.
        **kwargs : keyword arguments, optional
            If given, it is passed on to the function.
        """
        super().__init__(self.work)

        (self.pipeIn, self.pipeOut) = Pipe()
        self.process = Process(target=self.target, daemon=True,
            args=(self.pipeIn,function,)+args, kwargs=kwargs)

    def target(self, connection, function, *args, **kwargs):
        """
        This is executed as a new process.
        Alerts parent process via pipe.
        """
        try:
            result = function(*args, **kwargs)
            connection.send('RESULT')
            connection.send(result)
        except Exception as exception:
            connection.send('EXCEPTION')
            connection.send(exception)

    def work(self, *args, **kwargs):
        """
        This is executed as a new QThread.
        Fetches process results via pipe.
        """
        self.process.start()
        #? catch EOFError? thrown by pipe end
        check = self.pipeOut.recv()
        if check == 'RESULT':
            result = self.pipeOut.recv()
            self.process.join()
            return result
        elif check == 'EXCEPTION':
            exception = self.pipeOut.recv()
            # self.process.join()
            raise exception
