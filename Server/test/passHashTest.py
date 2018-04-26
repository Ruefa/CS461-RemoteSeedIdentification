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


# Tests for passHash
def test_passhash():
    #------------#
    # Unit Tests #
    #------------#

    # Normal password
    _test(b'Password123&$#') 
    print('Normal password test passed')

    # Empty password
    _test(b'')
    print('Empty password test passed')

    # Very short(tm) password
    _test(b'a')
    print('Short password test passed')

    # Stupidly long canadian password
    _test(b' eh '.join(b'word' for _ in range(1000)))
    print('Long password test passed')

test_passhash()
