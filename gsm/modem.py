import re
import time
import threading
import traceback
import Queue
import sys

from datetime import datetime

from pygsm import GsmModem

from gsm import port
from gsm import patterns


class Modem(GsmModem):
    _incoming = None
    _ihandler = None
        
    def __init__(self, *args, **kwargs):
        if 'control_port' in kwargs:
            control_port = kwargs.pop('control_port')
            self._control = port.ControlPort()
            self._control.connect(handlers=[(patterns.CALLER_ID, 
                                             self._caller_id)])
            self._outgoing = Queue.Queue()
        GsmModem.__init__(self, *args, **kwargs)
        
    def send(self, number=None, text=None, ussd=None):
        if number and text:
            self._outgoing.put(('sms', (number, text)))
            print 'outgoing sms to <%s> queued' % number
        elif ussd:
            self._outgoing.put(('ussd', ussd))
            print 'outgoing ussd <%s> queued' % ussd
        else:
            raise 'Invalid'
    
    def clear_read_messages(self, debug=False):
        s = self.query('AT+CMGD=?')
        if "error" in s.lower():
            print "Error - phone not supported"
        else:
            if debug:
                #+CMGD: (0,1),(0-4)
                print s
            match = re.search(r'\+CMGD: \(([^\)]+)\),\((\d)-(\d)\)', s)
            if match:
                xs = [int(x) for x in match.group(1).split(',')]
#                n = int(match.group(1))
                if debug:
                    print 'To delete is: %s' % xs
                for i in xs:
                    try:
                        temp = self.command('AT+CMGR=' + str(i+1)+',1')
                        if "REC READ" in temp[0]:
                            self.query('AT+CMGD=' + str(i+1))
                    except: pass

    def start(self, incoming_queue=None):
        if not self._ihandler:
            self._ihandler = IncomingHandler(self, incoming_queue)
            self._ihandler.start()
            self._ohandler = OutgoingHandler(self, self._outgoing)
            self._ohandler.start()
        else:
            raise 'Already started'
    
    def stop(self):
        if self._ihandler:
            self._ihandler.stop()
            self._ihandler = None
            self._ohandler.stop()
            self._ohandler = None
        else:
            raise 'Not started'
        
    def _caller_id(self, port, message):
        t = datetime.now()
        m = patterns.CALLER_ID.search(message)
        print '"%s" is calling on port: %s' % (m.group(1), port)
        #TODO: propagate this up
        self._incoming.put(('call', t, m.group(1)))
        

class OutgoingHandler(threading.Thread):
    """ControlPortHandler thread."""
    def __init__(self, modem, queue, interval=1):
        self.modem = modem
        self.queue = queue
        self.active = True
        self.interval = interval
        threading.Thread.__init__(self)

    def run(self):
        """Keep handling messages while active attribute is set."""
        while self.active:
            print 'Handling ...'
            try:
                print 'trying now .....'
                kind, data = self.queue.get()
                print 'got some data'
                self.modem.wait_for_network()
                if 'sms' is kind:
                    number, text = data
                    self.modem.send_sms(number, text)
                elif 'ussd' is kind:
                    raise 'Not implemented yet'
            except KeyboardInterrupt:
                self.stop() 
            finally:
                time.sleep(self.interval)

    def stop(self):
        self.active = False
        self.queue.put('') 


class IncomingHandler(threading.Thread):
    """ControlPortHandler thread."""
    def __init__(self, modem, queue, interval=2):
        self.modem = modem
        self.queue = queue
        self.interval = interval
        self.active = True
        threading.Thread.__init__(self)

    def run(self):
        """Keep handling messages while active attribute is set."""
        while self.active:
            try:
                print 'Checking for next message...'
                message = self.modem.next_message()
                if message is not None:
                    print 'We got a message: %s' % message
                    self.queue.put(message)
            except KeyboardInterrupt:
                print 'Ctrl-c received! Sending kill signal ...'
                self.stop()
            except Exception, x:
                print >>sys.stderr, "ERROR MODEM POLLING", x
                print >>sys.stderr, "".join(
                    traceback.format_exception(*sys.exc_info()))
                print >>sys.stderr, "-" * 20
            finally:
                time.sleep(self.interval)

    def stop(self):
        self.active = False