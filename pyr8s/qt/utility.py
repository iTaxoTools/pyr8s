"""Utility functions for PyQt5"""

import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui

import sys
import io
import logging
import multiprocessing

##############################################################################
### Widgets

class SyncedWidget(QtWidgets.QWidget):
    """Sync height with other widgets"""
    syncSignal = QtCore.pyqtSignal()

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

class UToolBar(QtWidgets.QToolBar, SyncedWidget):
    syncSignal = QtCore.pyqtSignal()
    pass

##############################################################################
### Logging

class PipeIO(io.IOBase):
    """File-like object that writes to a pipe connection"""
    # There are possibly better waiys to do this
    # using multiprocessing.connection.fileno()
    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.buffer = ''

    def close(self):
        self.connection.close()

    def fileno(self):
        return self.connection.fileno()

    def writable(self):
        return True

    def write(self, text):
        temp = self.buffer + text
        self.buffer = ''
        for line in temp.splitlines(True):
            if line[-1] == '\n':
                self.connection.send(line)
            else:
                self.buffer += line

    def writelines(self, lines):
        for line in lines:
            self.connection.send(line)

    def flush(self):
        # print('FLUSH')
        if self.buffer != '':
            self.connection.send(self.buffer)
        self.buffer = ''

class TextEditLogger(QtWidgets.QPlainTextEdit):
    """Thread-safe log display in a QPlainTextEdit"""
    appendRecord = QtCore.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.handler = logging.Handler()
        self.handler.emit = self.emit
        self.appendRecord.connect(self.appendTextInline)

    def appendTextInline(self, text):
        self.moveCursor(QtGui.QTextCursor.End);
        self.insertPlainText(text);
        self.moveCursor(QtGui.QTextCursor.End);

    def emit(self, record):
        text = self.handler.format(record)
        self.appendRecord.emit(text)

##############################################################################
### Multiprocessing

class UThread(QtCore.QThread):
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
    done = QtCore.pyqtSignal(object)
    fail = QtCore.pyqtSignal(object)

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
            print('WE ARE DONE')
            self.done.emit(result)


class UProcess(QtCore.QThread):
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
    done = QtCore.pyqtSignal(object)
    fail = QtCore.pyqtSignal(object)
    out = QtCore.pyqtSignal(object)
    err = QtCore.pyqtSignal(object)

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
        super().__init__()
        self.pipeControl = multiprocessing.Pipe(duplex=True)
        self.pipeData = multiprocessing.Pipe(duplex=True)
        self.pipeOut = multiprocessing.Pipe(duplex=False)
        self.pipeErr = multiprocessing.Pipe(duplex=False)
        self.pipeIn = multiprocessing.Pipe(duplex=False)
        self.process = multiprocessing.Process(
            target=self.target, daemon=True,
            args=(function,)+args, kwargs=kwargs)

    def target(self, function, *args, **kwargs):
        """
        This is executed as a new process.
        Alerts parent process via pipe.
        """
        self.pipeIn[1].close()
        self.pipeControl = self.pipeControl[1]
        self.pipeData = self.pipeData[1]
        self.pipeOut = self.pipeOut[1]
        self.pipeErr = self.pipeErr[1]
        self.pipeIn = self.pipeIn[0]

        self.pipeOut.send('THIS IS A TEST')
        self.pipeOut.send('ANOTHER ONE\n')
        self.pipeOut.send('SHOULD BE NEW LINE')

        file = PipeIO(self.pipeOut)
        file.write('AHA')
        file.write('OHO')
        file.write('NOLINE')
        file.write('NA-AH')

        import sys
        sys.stdout = file

        print('TESTIN')


        try:
            result = function(*args, **kwargs)
            self.pipeControl.send('RESULT')
            self.pipeData.send(result)
        except Exception as exception:
            self.pipeControl.send('EXCEPTION')
            self.pipeData.send(exception)

    def run(self):
        """
        Overloads QThread. This is run on a new thread.
        Do not call this directly, call self.start() instead.
        Starts and watches the process.
        """
        self.process.start()
        self.pipeData[1].close()
        self.pipeOut[1].close()
        self.pipeErr[1].close()
        self.pipeControl = self.pipeControl[0]
        self.pipeData = self.pipeData[0]
        self.pipeOut = self.pipeOut[0]
        self.pipeErr = self.pipeErr[0]
        self.pipeIn = self.pipeIn[1]

        waitList = {
            self.pipeControl: self.handleControl,
            self.pipeOut: self.handleOut,
            self.pipeErr: self.handleErr,
            }
        while waitList:
            for pipe in multiprocessing.connection.wait(waitList.keys()):
                try:
                    data = pipe.recv()
                except EOFError:
                    waitList.pop(pipe)
                else:
                    waitList[pipe](data)
        # Nothing left to do
        return

    def handleControl(self, data):
        # Exceptions caught by UThread
        if data == 'RESULT':
            result = self.pipeData.recv()
            self.done.emit(result)
            self.process.join()
        elif data == 'EXCEPTION':
            exception = self.pipeData.recv()
            self.fail.emit(exception)
            self.process.join()

    def handleOut(self, data):
        self.out.emit(data)

    def handleErr(self, data):
        self.err.emit(data)

    def quit(self):
        """Clean exit"""
        self.process.terminate()
        super().quit()
