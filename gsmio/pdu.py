#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


def encode(text, padding=0):
    return _pack_septets(text, padding).encode('hex').upper()

def decode(pdu, padding=0):
    return _unpack_septets(pdu, padding)

def _pack_septets(str, padding=0):
    bytes=[ord(c) for c in str]
    bytes.reverse()
    asbinary = ''.join([_to_binary(b)[1:] for b in bytes])
    # add padding
    for i in range(padding):
        asbinary+='0'
    
    # zero extend last octet if needed
    extra = len(asbinary) % 8
    if extra>0:
        for i in range(8-extra):
            asbinary='0'+asbinary
        
    # convert back to bytes
    bytes=[]
    for i in range(0,len(asbinary),8):
        bytes.append(int(asbinary[i:i+8],2))
    bytes.reverse()
    return ''.join([chr(b) for b in bytes])

def _unpack_septets(seq,padding=0):
    """ 
    this function taken from:
    http://offog.org/darcs/misccode/desms.py

    Thank you Adam Sampson <ats@offog.org>!
    """

    # Unpack 7-bit characters
    msgbytes,r = _consume_bytes(seq,len(seq)/2)
    msgbytes.reverse()
    asbinary = ''.join(map(_to_binary, msgbytes))
    if padding != 0:
        asbinary = asbinary[:-padding]
    chars = []
    while len(asbinary) >= 7:
        chars.append(int(asbinary[-7:], 2))
        asbinary = asbinary[:-7]
    return "".join(map(chr, chars))

def _consume_bytes(seq, num=1):
    """
    consumes bytes for num ints (e.g. 2-chars per byte)
    coverts to int, returns tuple of  ([byte...], remainder)
    """
    bytes=[]
    for i in range(0, _B(num), 2):
        bytes.append(int(seq[i:i+2],16))
    
    return (bytes,seq[_B(num):])

def _B(slot):
    """Convert slot to Byte boundary"""
    return slot * 2

def _to_binary(n):
    s = ''
    for i in range(8):
        s = ('%1d' % (n & 1)) + s
        n >>= 1
    return s



if __name__ == "__main__":
    
    pdus = [
        "AAD86C3602",
        "D9775D0E0A8FC7EFBA9B0E1287D961F7B80C4ACF4130170C063A22872E10F50D07"
        "55E1A07B9A8E061D914319C8040A8BDFF63288FE2687F32013A8EC56BFF3207498"
        "6D06C1E5E97119F47683826939BDCC068DC36CF61C444FB3D920E7FBED06D1D1E9"
        "39685A7793C379"
    ]
    
    text = [
        "*133#",
        "Your account balance is 0.00 GHC. Top Up with GHC2 & above "
        "today & enjoy half price on Airtel calls till Noon this Sunday",
    ]

    for i in range(len(pdus)):
        print decode(pdus[i]) == text[i]
        print encode(text[i]) == pdus[i]
        
        




