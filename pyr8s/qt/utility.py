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
            result = self.function(*self.args, **self.kwargs)
        except Exception as exception:
            self.fail.emit(exception)
        else:
            self.done.emit(result)

class UProcess(UThread):
    """
    Multiprocess function execution using PyQt5.
    Unlike QtCore.QProcess, this launches python functions, not programs.
    Use self.start() to fork/spawn.

    Example
    ----------

    def work(number):
        print('This runs on the child process.')
        print('Trying to use PyQt in here won\'t work.')
        return number * 2

    def success(result):
        print('This runs on the parent process.')
        print('You can spawn dialog messages here.')
        QMessageBox.information(None, 'Success',
            'Result = '+str(result), QMessageBox.Ok)
        print('This prints 42: ', result)

    self.process = UProcess(work, 21)
    self.process.done.connect(success)
    self.process.start()
    return

    """
    done = pyqtSignal(object)
    fail = pyqtSignal(object)

    def __getstate__(self):
        """Required for process spawning."""
        state = self.__dict__
        return state

    def __setstate__(self, state):
        """Required for process spawning."""
        # super(UProcess, self).__init__(None)
        self.__dict__ = state
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
        self.pipeData = Pipe(duplex=True)
        self.pipeOut = Pipe(duplex=False)
        self.pipeErr = Pipe(duplex=False)
        self.pipeIn = Pipe(duplex=False)
        self.process = Process(target=self.target, daemon=True,
            args=(function,)+args, kwargs=kwargs)

    def target(self, function, *args, **kwargs):
        """
        This is executed as a new process.
        Alerts parent process via pipe.
        """
        self.pipeIn[1].close()
        self.pipeData = self.pipeData[1]
        self.pipeOut = self.pipeOut[1]
        self.pipeErr = self.pipeErr[1]
        self.pipeIn = self.pipeIn[0]

        result = self.pipeIn.recv()
        print('CHILD SAYS THAT', result)
        try:
            result = function(*args, **kwargs)
            self.pipeData.send('RESULT')
            self.pipeData.send(result)
        except Exception as exception:
            self.pipeData.send('EXCEPTION')
            self.pipeData.send(exception)

    def work(self, *args, **kwargs):
        """
        This is executed as a new QThread.
        Starts and watches the process.
        Fetches process results via pipe.
        """
        self.process.start()
        self.pipeData[1].close()
        self.pipeOut[1].close()
        self.pipeErr[1].close()
        self.pipeData = self.pipeData[0]
        self.pipeOut = self.pipeOut[0]
        self.pipeErr = self.pipeErr[0]
        self.pipeIn = self.pipeIn[1]
        self.pipeIn.send('PARENT SAYS HI')
        #? catch EOFError? thrown by pipe end
        check = self.pipeData.recv()
        if check == 'RESULT':
            result = self.pipeData.recv()
            self.process.join()
            return result
        elif check == 'EXCEPTION':
            exception = self.pipeData.recv()
            # self.process.join()
            raise exception

    def quit(self):
        """Clean exit"""
        self.process.terminate()
        super().quit()
