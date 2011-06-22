import sys
import time
import threading
import traceback

import Queue

DEFAULT = 'default'

class Gateway(object):
    """The GSM Gateway itself.
    
    Provides an incoming queue which is filled with messages coming from 
    multiple devices, and an outgoing queue which is filled with messages
    intended to be sent from named or the default device.
    
    The data ports of the devices take the incoming queue of the gateway
    and populate it with incoming messages, as it happens. 
    
    Once an incoming message is added to the gateway's incoming queue, the 
    handle method of all regsitered handlers are called with the message.
    """
    
    handlers = []
    interval = 2
    incoming = Queue.Queue()
    _ihandler = None
        
    def __init__(self, devices_dict):
        self.devices_dict = devices_dict
        self.devices = devices_dict.values()
        self.default_device = devices_dict.get(DEFAULT) or self.devices[0]

    def add_handler(self, handler):
        self.handlers.append(handler)

    def send(self, number, text, modem=DEFAULT):
        self.get_modem(modem).send(number, text)

    def clear_read_messages(self):
        for modem in self.devices:
            modem.clear_read_messages(debug=True)
        
    def start(self):
        """Start the gateway."""
        self._ihandler = IncomingHandler(queue=self.incoming,
                                         gateway=self)
        for modem in self.devices:
            modem.start(incoming_queue=self.incoming)

    def stop(self):
        """Remove all pending tasks and stop the Gateway."""
        for modem in self.devices:
            modem.stop()

    def get_modem(self, key):
        if key is DEFAULT:
            return self.default_device
        return self.devices_dict.get(key)
    

class IncomingHandler(threading.Thread):
    """IncomingHandler thread."""
    def __init__(self, queue, gateway, interval=1):
        self.gateway = gateway
        self.queue = queue
        self.active = True
        self.interval = interval
        threading.Thread.__init__(self)

    def run(self):
        """Keep handling messages while active attribute is set."""
        while self.active:
            try:
                print 'trying now .....'
                message = self.queue.get()
                print 'Received a new message'
                for handler in self.gateway.handlers:
                    handler.handle(message)
            except KeyboardInterrupt:
                self.stop() 
            finally:
                time.sleep(self.interval)

    def stop(self):
        self.active = False
        self.queue.put('') 