#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import sys
import random

from gsm import Modem
from gsm import Gateway

from datetime import datetime, timedelta
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
                   logger=logger,
                   id='Airtel').boot()
                   
    mtn = Modem(port='/dev/cu.HUAWEIMobile-71',
                control_port='/dev/cu.HUAWEIMobile-72',
                logger=logger,
                id='MTN').boot()
    
    for m in [mtn, airtel]:
        m.clear_read_messages()

    # e160 specific configuration
#    for cmd in ["ATQ0 V1 E1 S0=0 &C1 &D2 +FCLASS=0",
#                "AT+CNMI= 2,0,0,2,0"
#                ]:
#        mtn.command(cmd, raise_errors=False)            
    
    return {'airtel': airtel, 'mtn': mtn}

def send_messages(app, n=5, test_phone='0266688206'):
    xs = ['hello', 'how are you', 'wikid!', 'wohoo', 'got it!']
    for s in [xs[random.randint(0, len(xs) - 1)] for i in range(n)]:
        app.send(test_phone, s)

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
    now = datetime.now()
    schedule = set([now + timedelta(minutes=random.randint(1, 10)) \
                    for i in range(10)])
    for count, t in [(random.randint(1, 4), (t.hour, t.minute)) \
                     for t in schedule]:
        add_task('send messages',
                 action=send_messages,
                 timeonday=t,
                 args=[app, count, '0263119161'])
        print 'Added task with %s msgs for %s' % (count, list(t))
    return scheduler
    
def main():
    import optparse
    import random
    
    p = optparse.OptionParser() 
    p.add_option('--port', '-p', default=None) 
    p.add_option('--clear_messages', '-c', default=None) 
    options, arguments = p.parse_args() 
    modems, gateway, app = bootstrap(options)
#    scheduler = setup_random_messages(app)
    
    gateway.start()
#    scheduler.start()
    

#    app.send('432', '2u 0263119161 0.5 1234')
    print 'done'
    
    
if __name__ == "__main__":
    main()
    sys.exit(0)