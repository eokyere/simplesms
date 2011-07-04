import phonenumbers

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

MESSAGES = ['Better Ghana', 
            'Vote for development', 
            'Be bold ;)']

def network (phone_number):
    try:
        key = '0%s' % sanitize_number(phone_number)[4:6]
        if key in NETWORK_MAP:
            return NETWORK_MAP[key]
    except: pass
    return 'Unknown'

def sanitize_number(number):
    return phonenumbers.format_number(phonenumbers.parse(number, "GH"), 
                                      phonenumbers.PhoneNumberFormat.E164)
