AIRTEL = 'Airtel'
MTN = 'MTN'
VODAFONE = 'Vodafone'
TIGO = 'Tigo'
EXPRESSO = 'Expresso'

NETWORKS = [AIRTEL, MTN, VODAFONE, TIGO, EXPRESSO]

NETWORK_MAP = {'026': AIRTEL, 
               '024': MTN,
               '054': MTN,
               '020': VODAFONE,
               '027': TIGO,
               '057': TIGO,
               '028': EXPRESSO}

MESSAGES = ['Better Ghana', 'Vote for development',
            'Be bold ;)']

def network (phone_number):
    if phone_number.startswith('+233'):
        key = '0%s' % phone_number[4:6]
    else:
        key = phone_number[:3]
    
    if key in NETWORK_MAP:
        return NETWORK_MAP[key]
    return 'Unknown'

def sanitize_phone_number(phone_number):
    return phone_number