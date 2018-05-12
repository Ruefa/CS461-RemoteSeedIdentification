import sys
import os
sys.path.append(os.path.abspath('..'))

from passHash import *

# Test a single iteration of hashPassword and checkPassword with the given password
def _test(p):
    h = hashPassword(p)
    assert len(h) == 80 # 16 byte salt + 64 byte hash
    assert checkPassword(p, h)
    assert not checkPassword(b'Not It', h)
    print('Pass\n')


# Tests for passHash
def test_passhash():
    #------------#
    # Unit Tests #
    #------------#

    # Normal password
    print('Testing normal password...')
    _test(b'Password123&$#') 

    # Empty password
    print('Testing empty password...')
    _test(b'')

    # Very short(tm) password
    print('Testing short password...')
    _test(b'a')

    # Stupidly long canadian password
    print('Testing long password...')
    _test(b' eh '.join(b'word' for _ in range(1000)))

test_passhash()
