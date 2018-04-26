import hashlib
import os

# Slower the better for security. These parameters are, near as I can tell, 
# solidly at or above what is standard. May need to reduce them to speed it up
# if we aren't happy with how long it is taking.
saltLen = 16
hashName = 'sha512'
iterations = 100000


# Generate and return a salt and hash for the given password.
# The salt is prepended on to the hash so we have a single hash value
# Uses pbkdf2_hmac, which is pretty standard
def hashPassword(password):
    s = os.urandom(saltLen)
    h = hashlib.pbkdf2_hmac(hashName, password, s, iterations)
    return s + h

# Validate a password against the passed in hash
def checkPassword(password, passHash):
    s, h = passHash[:16], passHash[16:]
    if h == hashlib.pbkdf2_hmac(hashName, password, s, iterations):
        return True
    return False

