#-----------------------------------------------------------------------------
# Commons - Utility classes for iTaxoTools modules
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


"""Utility functions for PySide6"""

from PySide6 import QtCore
from PySide6 import QtWidgets
from PySide6 import QtStateMachine
from PySide6 import QtGui

from contextlib import contextmanager

import sys, os
import multiprocessing

from . import io

##############################################################################
### Multiprocessing

class UThread(QtCore.QThread):
    """
    Multithreaded function execution using PySide6.
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
    done = QtCore.Signal(object)
    fail = QtCore.Signal(object)

    def __init__(self, function, *args, **kwargs):
        """
        Parameters
        ----------
        function : function
            The function to run on the new thread.
        \*args : positional arguments, optional
            If given, they are passed on to the function.
        \*\*kwargs : keyword arguments, optional
            If given, they are passed on to the function.
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


class UWorker():
    """
    Used by UProcess to spawn a new process.
    Holds pipe information for stdio redirection.
    """

    def __getstate__(self):
        """Required for process spawning."""
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        """Required for process spawning."""
        self.__dict__ = state

    def __init__(self, dict):
        dict['pipeIn'][1].close()
        self.pipeControl = dict['pipeControl'][1]
        self.pipeData = dict['pipeData'][1]
        self.pipeOut = dict['pipeOut'][1]
        self.pipeErr = dict['pipeErr'][1]
        self.pipeIn = dict['pipeIn'][0]

    def target(self, function, *args, **kwargs):
        """
        This is executed as a new process.
        Alerts parent process via pipe.
        """
        out = io.PipeIO(self.pipeOut, 'w')
        err = io.PipeIO(self.pipeErr, 'w')
        inp = io.PipeIO(self.pipeIn, 'r')

        # import sys
        sys.stdout = out
        sys.stderr = err
        sys.stdin = inp

        try:
            result = function(*args, **kwargs)
            self.pipeControl.send('RESULT')
            self.pipeData.send(result)
        except Exception as exception:
            self.pipeControl.send('EXCEPTION')
            self.pipeData.send(exception)
        finally:
            self.pipeControl.close()
            self.pipeData.close()
            self.pipeOut.close()
            self.pipeErr.close()
            self.pipeIn.close()


class UProcess(QtCore.QThread):
    """
    Multiprocess function execution using PySide6.
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
    done = QtCore.Signal(object)
    fail = QtCore.Signal(object)

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
        self._quit = None
        self.stream = None
        self.pipeControl = multiprocessing.Pipe(duplex=True)
        self.pipeData = multiprocessing.Pipe(duplex=True)
        self.pipeOut = multiprocessing.Pipe(duplex=False)
        self.pipeErr = multiprocessing.Pipe(duplex=False)
        self.pipeIn = multiprocessing.Pipe(duplex=False)
        self.worker = UWorker(self.__dict__)
        self.process = multiprocessing.Process(
            target=self.worker.target, daemon=True,
            args=(function,)+args, kwargs=kwargs)

    def setStream(self, stream):
        """Send process output to given file-like stream"""
        self.stream = stream

        if stream is not None:
            self.handleOut = self._streamOut
            self.handleErr = self._streamOut
        else:
            self.handleOut = self._streamNone
            self.handleErr = self._streamNone

    def _streamNone(self, data):
        pass

    def _streamOut(self, data):
        self.stream.write(data)


    def run(self):
        """
        Overloads QThread. This is run on a new thread.
        Do not call this directly, call self.start() instead.
        Starts and watches the process.
        """
        self._quit = False
        self.process.start()
        self.pipeData[1].close()
        self.pipeOut[1].close()
        self.pipeErr[1].close()
        self.pipeControl = self.pipeControl[0]
        self.pipeData = self.pipeData[0]
        self.pipeOut = self.pipeOut[0]
        self.pipeErr = self.pipeErr[0]
        self.pipeIn = self.pipeIn[1]

        sentinel = self.process.sentinel
        waitList = {
            sentinel: None,
            self.pipeControl: self.handleControl,
            self.pipeOut: self.handleOut,
            self.pipeErr: self.handleErr,
            }
        while waitList and sentinel is not None:
            for pipe in multiprocessing.connection.wait(waitList.keys()):
                if pipe == sentinel:
                    # Process exited, break loop after handling pipes
                    sentinel = None
                else:
                    try:
                        data = pipe.recv()
                    except EOFError:
                        waitList.pop(pipe)
                    else:
                        waitList[pipe](data)

        # Make sure process ended smoothly
        if self.process.exitcode != 0 and not self._quit:
            self.handleErr('Internal error!')
            exception = RuntimeError('Subprocess exited with error status ' +
                str(self.process.exitcode))
            self.fail.emit(exception)

    def handleControl(self, data):
        """Handle control pipe signals"""
        if data == 'RESULT':
            result = self.pipeData.recv()
            self.done.emit(result)
            self.process.join()
        elif data == 'EXCEPTION':
            exception = self.pipeData.recv()
            self.fail.emit(exception)
            self.process.join()

    def handleOut(self, data):
        """Overload this to handle process stdout"""
        pass

    def handleErr(self, data):
        """Overload this to handle process stderr"""
        pass

    def quit(self):
        """Clean exit"""
        self._quit = True
        if self.process is not None and self.process.is_alive():
            self.process.terminate()
        super().quit()


##############################################################################
### States and Events

class NamedEvent(QtCore.QEvent):
    """Custom event for use in state machines"""
    userEvent = QtCore.QEvent.registerEventType()
    events = set()
    def __init__(self, name, *args, **kwargs):
        """Pass name and args"""
        super().__init__(QtCore.QEvent.Type(self.userEvent))
        self.name = name
        self.args = args
        self.kwargs = kwargs
        # Avoid garbage-collection
        NamedEvent.events.add(self)

class NamedTransition(QtStateMachine.QAbstractTransition):
    """Custom transition for use in state machines"""
    def __init__(self, name):
        """Only catch events with given name"""
        super().__init__()
        self.name = name
    def eventTest(self, event):
        """Check for NamedEvents"""
        if event.type() == NamedEvent.userEvent:
            return event.name == self.name
        return False
    def onTransition(self, event):
        """Override virtual function"""
        # Allow event to be garbage-collected
        # NamedEvent.events.remove(event)
