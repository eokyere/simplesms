import re
import time
import threading
import traceback
import Queue
import sys

from datetime import datetime

from pygsm import GsmModem
from pygsm import errors


from simplesms import port
from simplesms import patterns
from simplesms import pdu as gsmpdu


class Modem(GsmModem):
    _incoming = None
    _ihandler = None
    id = None
    _outgoing = Queue.Queue()
        
    def __init__(self, *args, **kwargs):
        if 'control_port' in kwargs:
            control_port = kwargs.pop('control_port')
            self._control = port.ControlPort()
            self._control.connect(handlers=[(patterns.CALLER_ID, 
                                             self._caller_id),
                                             (patterns.USSD_RESPONSE,
                                              self._ussd_response)])
        if 'id' in kwargs:
            self.id = kwargs.pop('id')
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
                        temp = self.command('AT+CMGR=' + str(i) +',1')
                        if "REC READ" in temp[0]:
                            self.query('AT+CMGD=' + str(i))
                    except: pass

    def start(self, incoming_queue=None):
        if not self._ihandler:
            self._incoming = incoming_queue
            self._ihandler = IncomingHandler(self, self._incoming)
            self._ohandler = OutgoingHandler(self, self._outgoing)
            self._ihandler.start()
            self._ohandler.start()
        else:
            raise 'Already started'
        print '%s started!!!!' % self
    
    def stop(self):
        if self._ihandler:
            self._ihandler.stop()
            self._ohandler.stop()
            self._ihandler = None
            self._ohandler = None
        else:
            raise 'Not started'
        
    def _caller_id(self, port, message):
        t = datetime.now()
        m = patterns.CALLER_ID.search(message)
        self._incoming.put(('call', (self.id, m.group(1), t)))

    def _ussd_response(self, port, response):
        m = patterns.USSD_RESPONSE.search(response)
        if m:
            code, response, dcs = m.groups()
            self._incoming.put(('ussd_response', 
                                (self.id,
                                 gsmpdu.decode(response[2:-1]), 
                                 code, 
                                 dcs[1:])))

    def send_ussd(self, ussd=None, pdu=None, write_term="\r", 
                  raise_errors=True):
        
        """'
        A response looks like this:
        +CUSD: 0,"D9775D0E0A8FC7EFBA9B0E1287D961F7B80C4ACF4130170
        C063A22872E10F50D0755E1A07B9A8E061D914319C8040A8BDFF63288FE26
        87F32013A8EC56BFF32074986D06C1E5E97119F47683826939BDCC068DC36
        CF61C444FB3D920E7FBED06D1D1E939685A7793C379",15      
        """
        if pdu is None:
            if ussd:
                pdu = gsmpdu.encode(ussd)
            else:
                raise
              
        try:
            # run USSD code; the '1' indicates that we
            # want the result presented to us cast as string
            with self._modem_lock:
                self._write("AT+CUSD=1,\"%s\",15%s" % (str(pdu), write_term))
        except errors.GsmError, err:
            if not raise_errors:
                return None
            else:
                raise(err)
    
    def __repr__(self):
        return '<Modem %s>' % self.id   

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
            print 'Handling outgoing messages on %s ...' % self.modem
            try:
                kind, data = self.queue.get()
                print '<Network %s CSQ: %s>' % (self.modem.id,
                                                self.modem.wait_for_network())
                if 'sms' is kind:
                    self.modem.send_sms(*data)
                elif 'ussd' is kind:
                    self.modem.send_ussd(ussd=data)
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
                print '<Network %s CSQ: %s>' % (self.modem.id,
                                                self.modem.wait_for_network())
                print 'Checking for incoming message on %s ...' % self.modem
                message = self.modem.next_message()
                if message is not None:
                    self.queue.put(('sms', message))
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