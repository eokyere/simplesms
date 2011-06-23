#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

class Application(object):
    def __init__(self, gateway):
        self.gateway = gateway
        gateway.add_handler(self)
    
    def handle_sms(self, message):
        print 'We received [%s] from %s' % (message.text, message.sender)

    def handle_call(self, modem_id, caller, dt):
        print 'We received a call on %s from %s at %s' % (modem_id, caller, dt)
    
    def handle_ussd_response(self, modem_id, response, code, dcs):
        print '>>> USSD RESPONSE (%s): %s' % (modem_id, response)
    
    def send(self, *args, **kwargs): 
        self.gateway.send(*args, **kwargs)
        
def main():
    import optparse
    
    p = optparse.OptionParser() 
    p.add_option('--port', '-p', default=None) 
    options, arguments = p.parse_args() 
    
    modems, gateway = bootstrap(options)
    gateway.start()
    app = Application(gateway)
    app.send(modem_id='Airtel', ussd='*133#')
#    scheduler = setup_random_messages(app)
#    scheduler.start()
#    app.send('432', '2u 0263119161 0.5 1234')
    print 'done'


# __init__.py

from gsm import Modem
from gsm import Gateway


def bootstrap(options):
    modems = connect_modems(options)
    gateway = Gateway(modems)
    return (modems, gateway,)

def connect_modems(options):
    logger = Modem.debug_logger
    d = {}
    for id, data_port, control_port in get_modems(options):
        modem = Modem(id=id,
                      port=data_port,
                      control_port=control_port,
                      logger=logger).boot()
        d.update({id:modem})
    return d

def get_modems(options, id1='Airtel', id2='MTN'):
    import re
    import os
    modems = [(id1,
                '/dev/cu.HUAWEIMobile-Modem',
                '/dev/cu.HUAWEIMobile-Pcui',)]
    xs = ['/dev/%s' % x for x in os.listdir('/dev/') \
          if re.match(r'cu.HUAWEI.*-\d+', x)][:2]
    if xs:
        modems.append((id2, xs[0], xs[1]))
    return modems

def setup_random_messages(app):
    import random
    from kronos import method, ThreadedScheduler
    from datetime import datetime, timedelta
    
    def send_test_msgs(count, test_phone):
        xs = ['hello', 'how are you', 'wikid!', 'wohoo', 'got it!']
        for s in [xs[random.randint(0, len(xs) - 1)] for i in range(count)]:
            app.send(test_phone, s)

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
                 action=send_test_msgs,
                 timeonday=t,
                 args=[count, '0263119161'])
        print 'Added task with %s msgs for %s' % (count, list(t))
    return scheduler
    
if __name__ == "__main__":
    import sys
    main()
    sys.exit(0)