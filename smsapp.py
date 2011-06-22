#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import sys
import random

from gsm import Modem
from gsm import Gateway

from datetime import datetime
from kronos import method, ThreadedScheduler

class Application(object):
    def __init__(self, gateway):
        self.gateway = gateway
        gateway.add_handler(self)
    
    def handle(self, message):
        sender = message.sender
        text = message.text
        print 'We received [%s] from %s' % (text, sender)
    
    def send(self, number, text): 
        self.gateway.send(number, text)
        
def bootstrap(options):
    modems = connect_devices(options)
    gateway = Gateway(modems)
    app = Application(gateway)

    return (modems, gateway, app,)

def connect_devices(options):
    # setup modem(s)
    logger = Modem.debug_logger
    airtel = Modem(port=options.port or '/dev/cu.HUAWEIMobile-Modem',
                   control_port='/dev/cu.HUAWEIMobile-Pcui',
                   logger=logger).boot()
    return {'airtel': airtel}

def send_messages(app, n=5, test_phone='0266688206'):
    MSGS = ['hello', 'how are you', 'you are the man', 'wohoo']
    for i in range(n):
        app.send(test_phone, MSGS[random.randint(0, len(MSGS) - 1)])

def setup_random_messages(app):
    scheduler = ThreadedScheduler()

    def add_task(taskname, action, timeonday, args=[]):
        scheduler.add_daytime_task(action=action, 
                                   taskname=taskname, 
                                   weekdays=range(1,8),
                                   monthdays=None, 
                                   processmethod=method.threaded, 
                                   timeonday=timeonday,
                                   args=args, kw=None)
    
    schedule = list(set([(4,random.randint(37, 40)) for i in range(10)]))
    for count, timeonday in [(random.randint(1, 4), x) for x in schedule]:
        add_task('send messages',
                 action=send_messages,
                 timeonday=timeonday,
                 args=[app, count, '0263119161'])
        print 'Added task with %s msgs for %s' % (count, list(timeonday))
    return scheduler
    
def main():
    import optparse
    import random
    
    p = optparse.OptionParser() 
    p.add_option('--port', '-p', default=None) 
    p.add_option('--clear_messages', '-c', default=None) 
    options, arguments = p.parse_args() 
    modems, gateway, app = bootstrap(options)
    scheduler = setup_random_messages(app)
    
    gateway.start()
    scheduler.start()
    

#    app.send('432', '2u 0263119161 0.5 1234')
    print 'done'
    
    
if __name__ == "__main__":
    main()
    sys.exit(0)