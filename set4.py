from Crypto.Cipher import AES

import aes_modes
import mac
import sha1
import util


class ASCIIError(Exception):
    def __init__(self, ptxt):
        self.msg = ptxt

    def __str__(self):
        return 'Malformed txt: {}'.format(self.msg)


def check_ascii_compliant(msg):
    for c in msg:
        if ord(c) < 32:
            raise ASCIIError(msg)


def key_as_iv():
    key = util.gen_random_bytes(16)
    print 'The key is {}'.format(key.encode('hex'))
    msg = 'Super secret message unfortunately encrypted in a bad manner'

    ctxt = aes_modes.AES_CBC_encrypt(msg, key, key)
    c1 = ctxt[:AES.block_size]
    zeros = chr(0) * AES.block_size
    ctxt = c1 + zeros + c1 + ctxt[3*AES.block_size:]

    try:
        return check_ascii_compliant(aes_modes.AES_CBC_decrypt(ctxt, key, key))
    except ASCIIError as e:
        start = len('Malformed txt: ')
        ptxt = str(e)[start:]
        p1, p3 = ptxt[:AES.block_size], ptxt[2*AES.block_size:3*AES.block_size]
        return 'Recovered ' + util.xor(p1, p3).encode('hex')


def length_extension():
    msg = 'comment1=cooking%20MCs;userdata=foo;comment2=%20like%20a%20pound' \
          '%20of%20bacon'
    key = util.gen_random_bytes(16)
    auth = mac.sha1mac(key, msg)

    msglen = len(msg) + len(key)
    dummy = chr(0x00) * msglen
    s = sha1.SHA1()
    glue = s.pad(dummy)[msglen:]

    hs = []
    authval = int(auth, 16)
    while authval:
        hs = [int(authval & 0xFFFFFFFF)] + hs
        authval = authval >> 32

    inject = ';admin=true'
    tampered = sha1.SHA1(backdoored=True, backdoor=hs)
    forged = tampered.hash(dummy + glue + inject)

    try:
        if mac.authenticate(key, msg + glue + inject, forged):
            return 'Successfully Forged Message!\n' \
                   'Message: {}\nMAC: {}'.format(msg + glue + inject, forged)
        else:
            return 'Message Forgery Failed'
    except:
        return 'Message Forgery Failed'


def sha1mac():
    msg = 'Some super secret thing I dont want to share'
    key = util.gen_random_bytes(16)
    auth = mac.sha1mac(key, msg)
    testpassed = 0

    try:
        assert(mac.authenticate(key, msg, auth) == True)
        testpassed += 1
        print 'Correct MAC accepted'
    except:
        print 'Correct MAC erroneously rejected'
    try:
        badauth = mac.sha1mac(util.gen_random_bytes(16), msg)
        assert(mac.authenticate(key, msg, badauth) == True)
        print 'Tampered MAC erroneously accepted'
    except:
        testpassed += 1
        print 'Tampered MAC rejected'
    try:
        badmsg = 'I didnt write this'
        assert(mac.authenticate(key, badmsg, auth) == True)
        print 'Tampered message erroneously accepted'
    except:
        testpassed += 1
        print 'Tampered message rejected'

    if testpassed == 3:
        return 'All Tests Passed!'
    else:
        return 'Not All Tests Passed :('