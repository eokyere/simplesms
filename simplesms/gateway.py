import sys
import time
import threading
import traceback

import Queue

DEFAULT = 'default'

class Gateway(object):
    """The GSM Gateway itself.
    
    Provides a queue which is populated with incoming messages, calls and 
    ussd responses coming from multiple devices, and another queue which is 
    populated with messages intended to be sent from a named or default device.
    """
    def __init__(self, devices_dict, default_device=None):
        self.incoming = Queue.Queue()
        self._ihandler = None
        self.handlers = []
        self.interval = 2
        self.devices_dict = devices_dict
        self.devices = devices_dict.values()
        self.default_device = default_device or \
                              devices_dict.get(DEFAULT) or self.devices[0]

    def add_handler(self, handler):
        self.handlers.append(handler)

    def send(self, number=None, text=None, ussd=None, modem_id=DEFAULT):
        if number and text:
            self.get_modem(modem_id).send(number, text)
        elif ussd:
            self.get_modem(modem_id).send(ussd=ussd)
        else:
            raise 'Invalid'

    def clear_read_messages(self):
        for modem in self.devices:
            modem.clear_read_messages(debug=True)
        
    def start(self, clear_messages=False):
        """Start the gateway."""
        self._ihandler = GatewayIncomingHandler(queue=self.incoming,
                                                gateway=self)
        for modem in self.devices:
            modem.start(incoming_queue=self.incoming)
        if clear_messages:
            self.clear_read_messages()
        self._ihandler.start()
        

    def stop(self):
        """Remove all pending tasks and stop the Gateway."""
        for modem in self.devices:
            modem.stop()

    def get_modem(self, key):
        if key is DEFAULT:
            return self.default_device
        return self.devices_dict.get(key)
    

class Handler(object):

    def __init__(self, gateway):
        self.gateway = gateway
        gateway.add_handler(self)

    def send(self, *args, **kwargs): 
        self.gateway.send(*args, **kwargs)
    
    def handle_sms(self, message):
        pass
    
    def handle_call(self, modem_id, caller, dt):
        print 'We received a call on %s from %s at %s' % (modem_id, caller, dt)
    
    def handle_ussd_response(self, modem_id, response, code, dcs):
        print '>>> USSD RESPONSE (%s): %s' % (modem_id, response)
        

class GatewayIncomingHandler(threading.Thread):
    """GatewayIncomingHandler thread."""
    def __init__(self, queue, gateway, interval=2):
        self.gateway = gateway
        self.queue = queue
        self.active = True
        self.interval = interval
        threading.Thread.__init__(self)

    def run(self):
        """Keep handling messages while active attribute is set."""
        while self.active:
            try:
                kind, data = self.queue.get()
                for handler in self.gateway.handlers:
                    if 'sms' is kind:
                        handler.handle_sms(data)
                    elif 'call' is kind:
                        handler.handle_call(*data)
                    elif 'ussd_response' is kind:
                        handler.handle_ussd_response(*data)
            except KeyboardInterrupt:
                self.stop() 
            finally:
                time.sleep(self.interval)

    def stop(self):
        self.active = False
        self.queue.put('') 