import random
import string

passLen = 8
alphanumeric = string.ascii_letters + string.digits

def makePassword(length = passLen, chars = alphanumeric):
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length)).encode()
