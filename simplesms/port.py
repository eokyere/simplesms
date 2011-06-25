"""This module defines the Port classes.
"""

__author__ = 'Emmanuel Okyere <chief@hutspace.net>'

import os
import time
import threading
import Queue

import serial
from pygsm import errors

from simplesms import patterns
from simplesms import settings


class Port(object):
    _port = None
    
    def _write(self, cmd):
        """Write a string to the modem."""

        #self._log(repr(str_), "write")

        try:
            self._port.write(cmd + '\r')

        # if the device couldn't be written to,
        # wrap the error in something that can
        # sensibly be caught at a higher level
        except OSError, err:
            raise(errors.GsmWriteError)


class ControlPort(Port):
    """Responsible queuing/handling of control port data."""

    def __init__(self, port=settings.CONTROL_PORT, 
                 timeout=settings.CONTROL_PORT_TIMEOUT, speed=9600,
                 caller_id=True):
        self._port = serial.Serial(port, speed, timeout=timeout)
        if caller_id:
            self._write('AT+CLIP=1')
        self._lock = threading.Lock()
        self.queue = Queue.Queue()
        self.handlers = None
        self._handler = None
        self._reader = None

    def connect(self, handlers=None):
        """Connect the port.
        """
        if self._reader:
            raise 'Port already started.'
        self.handlers = handlers or patterns.DEFAULT_HANDLERS
        return self._start()

    def disconnect(self):
        """Disconnect the port."""
        if self._reader:
            self._stop()
        else:
            raise 'Port not connected.'

    def _start(self):
        """Start listening on the control port."""
        print 'Starting feeder ...'
        self._reader = ControlPortReader(self.queue, self._port, self._lock)
        self._reader.start()
        print 'Starting handler ...'
        self._handler = ControlPortHandler(self, self.queue, self.handlers)
        self._handler.start()
        return self
    
    def _stop(self):
        self._handler.stop()
        self._reader.stop()
        self._reader = None


class ControlPortHandler(threading.Thread):
    """ControlPortHandler thread."""
    def __init__(self, port, queue, handlers):
        self.port = port
        self.queue = queue
        self.handlers = handlers
        self.active = True
        threading.Thread.__init__(self)

    def handle(self, message):
        """Match message pattern with an action to take.

        Arguments:
            message -- string received from the port.
        """
        for pattern, action in self.handlers:
            if pattern.search(message):
                action(self.port, message)
                break
        else:
            patterns.ignore(self.port, message)

    def run(self):
        """Keep handling messages while active attribute is set."""
        while self.active:
            try:
                self.handle(self.queue.get())
            except KeyboardInterrupt:
                print 'Ctrl-c received! Sending kill signal ...'
                self.stop()
    
    def stop(self):
        self.active = False
        self.queue.put('')
        

class ControlPortReader(threading.Thread):
    """Queue feeder thread."""
    def __init__(self, queue, _port, _lock):
        self.active = True
        self.queue = queue
        self._port = _port
        self._lock = _lock
        threading.Thread.__init__(self)

    def run(self):
        """Start the queue feeder thread."""
        while self.active:
            self._lock.acquire()
            try:
                self.queue.put(self._port.readline())
            except KeyboardInterrupt:
                print 'Ctrl-c received! Sending kill signal ...'
                self.stop()
            finally:
                self._lock.release()
                # Putting the thread on idle between releasing
                # and acquiring the lock for 100ms
                time.sleep(.1)

    def stop(self):
        """Stop the queue feeder thread."""
        self.active = False
        self._port.write('\r\n')