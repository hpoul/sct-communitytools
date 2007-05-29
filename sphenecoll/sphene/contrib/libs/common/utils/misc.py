"""
Most stuff here is borrowed from the zyons project (http://zyons.python-hosting.com/)
"""


from Crypto.Cipher import Blowfish
from base64 import *
import random



def cryptString( secret, plain ):
    obj = Blowfish.new( secret, Blowfish.MODE_ECB )
    #randstring = unicode(open("/dev/urandom").read(12), 'ascii', 'ignore')
    randstring = str.join( '', random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890',12) )
    split = random.randrange(10)+1
    s = randstring[:split] + ':valid:' + plain + ':valid:' + randstring[split:]
    length = len(s)

    l = length + 8 - ( length % 8 )
    padded = s + " " * ( 8 - length % 8 )

    ciph = obj.encrypt(padded[:l])
    try:
        return b32encode(ciph)
    except NameError:
        return encodestring


def decryptString( secret, cipher ):
    obj = Blowfish.new( secret, Blowfish.MODE_ECB )
    try:
        ciph = b32decode( cipher )
    except NameError:
        ciph = decodestring( cipher )

    plaintext = obj.decrypt( ciph )
    try:
        (c1,email,c2) = plaintext.split(":valid:")
    except ValueError:
        return None
    return email

