import re
import time
import threading
import traceback
import Queue
import sys

from datetime import datetime

from pygsm import GsmModem
from pygsm import errors


from gsm import port
from gsm import patterns
from gsm import pdu as gsmpdu


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
                                             self._caller_id)])
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
        print '>>>>> "%s" is calling on port: %s' % (m.group(1), port)
        #TODO: propagate this up
        self._incoming.put(('call', (t, m.group(1))))


    def send_ussd(self, ussd=None, pdu=None, read_term=None, read_timeout=10, 
                  write_term="\r", raise_errors=True):
        
        """'+CUSD: 0,"D9775D0E0A8FC7EFBA9B0E1287D961F7B80C4ACF4130170
        C063A22872E10F50D0755E1A07B9A8E061D914319C8040A8BDFF63288FE26
        87F32013A8EC56BFF32074986D06C1E5E97119F47683826939BDCC068DC36
        CF61C444FB3D920E7FBED06D1D1E939685A7793C379",15      
        """
        if pdu is None:
            if ussd:
                pdu = gsmpdu.encode(ussd)
            else:
                raise
              
        # keep looping until the command
        # succeeds or we hit the limit
        retries = 0
        while retries < self.max_retries:
            try:
                # run USSD code, and wait for the
                # response. the '1' indicates that we
                # want the result presented to us
                # cast as string -- don't want unicode here
                ussd_string = "AT+CUSD=1,\"%s\",15" % str(pdu) 
                with self._modem_lock:
                    self._write(ussd_string + write_term)
                    lines = self._seek(
                        "+CUSD:",
                        read_term=read_term,
                        read_timeout=read_timeout)

            except errors.GsmError, err:
                if not raise_errors:
                    return None
                else:
                    raise(err)

            # if the first line of the response echoes the cmd
            # (it shouldn't, if ATE0 worked), silently drop it
            if lines[0] == ussd_string:
                lines.pop(0)

            # remove all blank lines and unsolicited
            # status messages. i can't seem to figure
            # out how to reliably disable them, and
            # AT+WIND=0 doesn't work on this modem
            lines = [
                line
                for line in lines
                if line      != "" or\
                line[0:6] == "+WIND:" or\
                line[0:6] == "+CREG:" or\
                line[0:7] == "+CGRED:"]

            # parse out any incoming sms that were bundled with this data
            lines = self._parse_incoming_sms(lines)

            # rest up for a bit (modems are
            # slow, and get confused easily)
            time.sleep(self.cmd_delay)

            # don't send oddly encoded strings back
            try:
                lines = [line.encode('utf_8') for line in lines]
            except Exception, e:
                print e

            result_string = ""
            result_lines = []
            for line in lines:
                # AT+CUSD returns OK and then sends the response
                # after a brief interlude
                if line.startswith("OK"):
                    continue
                else:
                    result_lines.append(line)

            if len(result_lines) > 0:
                # response string from network can be multiline, so
                # flatten these lines into a single string
                m = re.match(r'.*\+CUSD: (\d)(,".+")?(,\d+)?', 
                             " ".join(result_lines))
                if m:
                    code, response, dcs = m.groups()
                    return (code, gsmpdu.decode(response[2:-1]), dcs[1:],)
            return None, None, None
    
    def _seek(self, token, read_term=None, read_timeout=None):
        buffer = []

        # keep on looping until a command terminator
        # is encountered. these are NOT the same as the
        # "read_term" argument - only OK or ERROR is valid
        # in addition to lines beginning with "token"
        while(True):
            buf = self._read(
                read_term=read_term,
                read_timeout=read_timeout).strip()
            buffer.append(buf)

            if buf.startswith(token):
                return buffer
            
            # some errors contain useful error codes, so raise a
            # proper error with a description from pygsm/errors.py
            m = re.match(r"^\+(CM[ES]) ERROR: (\d+)$", buf)
            if m is not None:
                type, code = m.groups()
                raise errors.GsmModemError(type, int(code))

            # ...some errors are not so useful
            # (at+cmee=1 should enable error codes)
            if buf == "ERROR":
                raise errors.GsmModemError     
            
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
                    number, text = data
                    # can i just say *args?
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
                print '<Network %s CSQ: %s>' % (self.modem.id,
                                                self.modem.wait_for_network())
                print 'Checking for incoming message on %s ...' % self.modem
                message = self.modem.next_message()
                if message is not None:
                    print 'We got a message: %s' % message
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