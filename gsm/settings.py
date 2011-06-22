# Darwin (MacOS X) systems.
DATA_PORT = '/dev/cu.HUAWEIMobile-Modem'
CONTROL_PORT = '/dev/cu.HUAWEIMobile-Pcui'

CONTROL_PORT_TIMEOUT = 0.5
BAUDRATE = '115200'

DIALNUM = '*99#'

PPPD_PATH = '/usr/sbin/pppd'
PPPD_PARAMS = ['modem', 'crtscts', 'defaultroute', 'usehostname', '-detach',
               'noipdefault', 'call', 'humod', 'user', 'ppp', 'usepeerdns',
               'idle', '0', 'logfd', '8']

import os
if os.name == 'posix':
    if 'linux' in os.sys.platform:
        # Linux systems. Already set.
        DATA_PORT = '/dev/ttyUSB0'
        CONTROL_PORT = '/dev/ttyUSB1'
        pass
    elif 'freebsd' in os.sys.platform:
        # FreeBSD systems.
        DATA_PORT = '/dev/ugen0'
        CONTROL_PORT = '/dev/ugen1'
#    elif os.sys.platform == 'darwin':
#        pass