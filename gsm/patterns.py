import re

INCOMING_CALL = re.compile(r'^RING\r\n')
CALLER_ID = re.compile(r'^\+CLIP: "\+?(\d+)",(\d+).*') 
USSD_RESPONSE = re.compile(r'^\+CUSD: (\d)(,".+")?(,\d+)?') 
SMS_RECEIVED = re.compile(r'^\+CMTI:.*')
RSSI_UPDATE = re.compile(r'^\^RSSI:.*')
FLOW_REPORT = re.compile(r'^\^DSFLOWRPT:')
MODE_UPDATE = re.compile(r'^\^MODE:.*')
BOOT_UPDATE = re.compile(r'^\^BOOT:.*$')
NEW_LINE = re.compile(r'^\r\n$')
EMPTY_LINE = re.compile(r'^$')

def ignore(port, message):
    pass

def hello(port, message):
    print 'hello'
    
def caller_id(port, message):
    #+CLIP: "0266688206",129,,,,0
    #+CLIP: <number>, <type>[ ,<subaddr>, <satype>, <alpha> ]
    m = CALLER_ID.search(message)
    print 'CLIP: <%s> is calling on port %s' % (m.group(1), port)

DEFAULT_HANDLERS = [
    (INCOMING_CALL, hello),
    (CALLER_ID, caller_id),
    (NEW_LINE, ignore),
    (EMPTY_LINE, ignore),
    (BOOT_UPDATE, ignore),
    (SMS_RECEIVED, hello),
    (MODE_UPDATE, ignore),
    (RSSI_UPDATE, ignore),
    (FLOW_REPORT, ignore)
]