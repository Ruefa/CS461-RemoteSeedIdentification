import pathlib
import time
import sys
import os
sys.path.append(os.path.abspath('..'))

from db import *
from passHash import *
from pony.orm import *

testDB = pathlib.Path(os.path.abspath('.')) / 'testdb' / 'testdb.sqlite'
testDB.parent.mkdir(exist_ok=True)

def resetDB():
    db.drop_all_tables(with_all_data=True)
    db.disconnect()
    db.create_tables()

def test_dbInit():
    print('Testing dbInit...')
    dbInit(testDB)
    #assert testDB.is_file()
    print('Pass\n')

def test_newAccount():
    try:
        initDB(testDB)
    except:
        resetDB()
    print('Testing new account...')
    def testNew(u, p):
        assert newAccount(u, p)
        u = u.lower()
        with db_session:
            a = Account[u]
            assert checkPassword(p, a.password)
            assert not a.sessionToken

    def testExisting(u):
        with db_session:
            a = Account[u]
        assert not newAccount(u, b'Not Real')
        with db_session:
            assert a.password == Account[u].password # Nothing changed

        
    #------------#
    # Unit Tests #
    #------------#
    
    # Normal account
    print('\tTesting normal account creation...')
    testNew(b'user@gmail.com', b'Pass')
    print('\tPass\n')

    # Existing account
    print('\tTesting already existing account...')
    with db_session:
        Account(username=b'i think', password=b'i exist')
    testExisting(b'i think')
    print('\tPass\n')

    print('\tTesting case insensitivity...')
    # Case insensitive
    testNew(b'BIG', b'pass')
    testExisting(b'big')
    print('\tPass\n')

    # Empty username
    print('\tTesting empty username...')
    testNew(b'', b'Pass')
    testExisting(b'')
    print('\tPass\n')

    # Very short username
    print('\tTesting short username...')
    testNew(b'a', b'Pass')
    testExisting(b'a')
    print('\tPass\n')

    # Very long username
    print('\tTesting long username...')
    u = b'why'.join(b' so long ' for _ in range(1000))
    testNew(u, b'Pass')
    testExisting(u)
    print('\tPass\n')

    # Passwords will always be the same length assuming passhash works properly
    # So no need to test that here
    
    # Non-bytes username
    print('\tTesting invalid data types...')
    print('\t\tString...')
    try:
        newAccount('String', b'Pass')
    except:
        print('\t\tPass\n')
    else:
        assert False # Fail

    print('\t\tInt...')
    try:
        newAccount(123, b'Pass')
    except:
        print('\t\tPass\n')
    else:
        assert False # Fail


def test_login():
    try:
        initDB(testDB)
    except:
        resetDB()
    print("Testing Login")
    def test(u, p):
        with db_session:
            Account(username=u.lower(), password=hashPassword(p))
        t = login(u, p)
        assert t
        assert len(t) == len(u) + tokenLen

    #------------#
    # Unit Tests #
    #------------#
    
    # Normal account
    print('\tTesting normal account login...')
    test(b'user@gmail.com', b'Pass')
    print('\tPass\n')

    print('\tTesting case insensitivity...')
    # Case insensitive
    test(b'BIG', b'pass')
    print('\tPass\n')

    # Empty username
    print('\tTesting empty username...')
    test(b'', b'Pass')
    print('\tPass\n')

    # Very short username
    print('\tTesting short username...')
    test(b'a', b'Pass')
    print('\tPass\n')

    # Very long username
    print('\tTesting long username...')
    u = b'why'.join(b' so long ' for _ in range(1000))
    test(u, b'Pass')
    print('\tPass\n')

    # Testing Bad credentials
    print('\tTesting bad password')
    assert not login(b'user@gmail.com', b'WRONG PASS')
    print('\tPass\n')

    print('\tTesting bad username')
    assert not login(b'Nope', b'WRONG PASS')
    print('\tPass\n')

    # Testing multiple logins
    print ('\tTesting multiple back to back logins...')
    test(b'mult', b'pass')
    t = login(b'mult', b'pass')
    assert t
    assert len(t) == len(b'mult') + tokenLen
    t = login(b'mult', b'pass')
    assert t and len(t) == len(b'mult') + tokenLen
    print('\tPass\n')

    # Testing newToken=False
    print('\tTest login without generating new token...')
    with db_session:
        Account(username=b'oldtoken', password=hashPassword(b'pass'))
    t = login(b'oldtoken', b'pass')
    assert t
    assert t == login(b'oldtoken', b'pass', newToken=False)
    print('\tPass\n')

    # Testing newToken=False, but no current login token
    print('\tTesting no token, but newToken is False...')
    with db_session:
        Account(username=b'oldtoken2', password=hashPassword(b'pass'))
    t = login(b'oldtoken2', b'pass', newToken=False)
    assert t
    assert len(t) == len(b'oldtoken2') + tokenLen
    print('\tPass\n')

def test_checkToken():
    try:
        initDB(testDB)
    except:
        resetDB()
    print("Testing Check Token...")

    #------------#
    # Unit Tests #
    #------------#

    print('\tTesting normal operation')
    t = os.urandom(tokenLen)
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'), sessionToken=t)
    assert checkToken(b'user', t)
    print('\tPass\n')

    print('\tTesting wrong username')
    with db_session:
        Account(username=b'user2', password=hashPassword(b'pass'))
    assert not checkToken(b'user2', t)
    print('\tPass\n')

    print('\tTesting wrong token')
    assert not checkToken(b'user', os.urandom(tokenLen))
    print('\tPass\n')

    print('\tTesting non-existant username')
    assert not checkToken(b'notreal', t)
    print('\tPass\n')

    print('\tTesting blank token')
    assert not checkToken(b'user2', None)
    assert not checkToken(b'user2', b'')
    print('\tPass\n')

def test_logout():
    try:
        initDB(testDB)
    except:
        resetDB()
    print('Test Logout...')

    #------------#
    # Unit Tests #
    #------------#
 
    print('\tTesting normal operation...')
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'), sessionToken=os.urandom(tokenLen))
    logout(b'user')
    with db_session:
        assert not Account[b'user'].sessionToken
    print('\tPass\n')

    print('\tTesting bad username...')
    # Shouldn't do anything except not crash
    try:
        logout(b'Fake')
    except:
        assert False
    print('\tPass\n')

def test_changePassword():
    try:
        initDB(testDB)
    except:
        resetDB()
    print('Test Change Password')
    
    #------------#
    # Unit Tests #
    #------------#

    print('\tTesting normal operation...')
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
    assert changePassword(b'user', b'ShinyAndNew')
    with db_session:
        assert checkPassword(b'ShinyAndNew', Account[b'user'].password)
    print('\tPass\n')

    print('\tTesting bad username...')
    assert not checkPassword(b'Fake', b'Pass')
    print('\tPass\n')

def test_newPassword():
    try:
        initDB(testDB)
    except:
        resetDB()
    print('Test New Password...')

    #------------#
    # Unit Tests #
    #------------#

    print('\tTesting normal operation...')
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
    newpass = newPassword(b'user')
    assert newpass
    assert newpass.isalnum()
    with db_session:
        assert checkPassword(newpass, Account[b'user'].password)
    print('\tPass\n')

    print('\tTesting bad username...')
    assert not newPassword(b'Fake')
    print('\tPass\n')

def test_newReport():
    try:
        initDB(testDB)
    except:
        resetDB()
    print('Test New Report...')

    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
        Account(username=b'user2', password=hashPassword(b'pass'))

    #------------#
    # Unit Tests #
    #------------#

    print('\tTesting normal operation...')
    rid = newReport(b'user')
    assert rid
    with db_session:
        r = Report[rid]
        assert not r.sourceImg
        assert not r.resultsImg
        assert not r.results
        assert not r.isAnalysisDone
    print('\tPass\n')

    print('\tTesting normal operation (different user)...')
    rid = newReport(b'user2')
    assert rid
    with db_session:
        r = Report[rid]
        assert not r.sourceImg
        assert not r.resultsImg
        assert not r.results
        assert not r.isAnalysisDone
    print('\tPass\n')

    print('\tTesting arguments...')

    print('\t\tsourceImg')
    path = 'path/path'
    rid = newReport(b'user', sourceImg=path)
    assert rid
    with db_session:
        r = Report[rid]
        assert path == r.sourceImg
        assert not r.resultsImg
        assert not r.results
        assert not r.isAnalysisDone
    print('\t\tPass\n')

    print('\t\tresultsImg')
    path = 'path/path'
    rid = newReport(b'user', resultsImg=path)
    assert rid
    with db_session:
        r = Report[rid]
        assert not r.sourceImg
        assert path == r.resultsImg
        assert not r.results
        assert not r.isAnalysisDone
    print('\t\tPass\n')
    
    print('\t\tresults')
    results = 'result string'
    rid = newReport(b'user', results=results)
    assert rid
    with db_session:
        r = Report[rid]
        assert not r.sourceImg
        assert not r.resultsImg
        assert results == r.results
        assert not r.isAnalysisDone
    print('\t\tPass\n')

    print('\t\tisAnalysisDone')
    rid = newReport(b'user', isAnalysisDone=True)
    assert rid
    with db_session:
        r = Report[rid]
        assert not r.sourceImg
        assert not r.resultsImg
        assert not r.results
        assert r.isAnalysisDone
    print('\t\tPass\n')

    print('\t\tAll')
    path = 'path/path'
    path2 = 'path/other/path'
    results = 'result string'
    rid = newReport(b'user', sourceImg=path, resultsImg=path2, results=results, isAnalysisDone=True)
    assert rid
    with db_session:
        r = Report[rid]
        assert path == r.sourceImg
        assert path2 == r.resultsImg
        assert results == r.results
        assert r.isAnalysisDone
    print('\t\tPass\n')

def test_updateReport():
    try:
        initDB(testDB)
    except:
        resetDB()
    print('Test Update Report...')

    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))

    rid = None

    #------------#
    # Unit Tests #
    #------------#

    print('\tTest optional arguments...')

    print('\t\tNone')
    path = 'path/path'
    path2 = 'path/other/path'
    results = 'result string'
    with db_session:
        r = Report(owner=Account[b'user'], sourceImg=path, resultsImg=path2, results=results, isAnalysisDone=True)
        commit()
        rid = r.id
    assert updateReport(rid)
    with db_session:
        r = Report[rid]
        assert path == r.sourceImg
        assert path2 == r.resultsImg
        assert results == r.results
        assert r.isAnalysisDone
    print('\t\tPass\n')

    print('\t\tsourceImg')
    path = 'path/path'
    path2 = 'path/other/path'
    results = 'result string'
    with db_session:
        r = Report(owner=Account[b'user'], sourceImg=path, resultsImg=path2, results=results, isAnalysisDone=True)
        commit()
        rid = r.id
    assert updateReport(rid, sourceImg=path2)
    with db_session:
        r = Report[rid]
        assert path2 == r.sourceImg
        assert path2 == r.resultsImg
        assert results == r.results
        assert r.isAnalysisDone
    print('\t\tPass\n')

    print('\t\tresultsImg')
    path = 'path/path'
    path2 = 'path/other/path'
    results = 'result string'
    with db_session:
        r = Report(owner=Account[b'user'], sourceImg=path, resultsImg=path2, results=results, isAnalysisDone=True)
        commit()
        rid = r.id
    assert updateReport(rid, resultsImg=path)
    with db_session:
        r = Report[rid]
        assert path == r.sourceImg
        assert path == r.resultsImg
        assert results == r.results
        assert r.isAnalysisDone
    print('\t\tPass\n')

    print('\t\tresults')
    path = 'path/path'
    path2 = 'path/other/path'
    results = 'result string'
    results2 = 'Other stuff'
    with db_session:
        r = Report(owner=Account[b'user'], sourceImg=path, resultsImg=path2, results=results, isAnalysisDone=True)
        commit()
        rid = r.id
    assert updateReport(rid, results=results2)
    with db_session:
        r = Report[rid]
        assert path == r.sourceImg
        assert path2 == r.resultsImg
        assert results2 == r.results
        assert r.isAnalysisDone
    print('\t\tPass\n')

    print('\t\tisAnalysisDone')
    path = 'path/path'
    path2 = 'path/other/path'
    results = 'result string'
    with db_session:
        r = Report(owner=Account[b'user'], sourceImg=path, resultsImg=path2, results=results, isAnalysisDone=False)
        commit()
        rid = r.id
    assert updateReport(rid, isAnalysisDone=True)
    with db_session:
        r = Report[rid]
        assert path == r.sourceImg
        assert path2 == r.resultsImg
        assert results == r.results
        assert r.isAnalysisDone
    print('\t\tPass\n')

    print('\t\tAll')
    path = 'path/path'
    path2 = 'path/other/path'
    results = 'result string'
    results2 = 'Other stuff'
    with db_session:
        r = Report(owner=Account[b'user'], sourceImg=path, resultsImg=path2, results=results, isAnalysisDone=False)
        commit()
        rid = r.id
    assert updateReport(rid, sourceImg=path2, resultsImg=path, results=results2, isAnalysisDone=True)
    with db_session:
        r = Report[rid]
        assert path2 == r.sourceImg
        assert path == r.resultsImg
        assert results2 == r.results
        assert r.isAnalysisDone
    print('\t\tPass\n')

    print('\tTest bad ID...')
    assert not updateReport(1000)
    print('\tPass\n')

def test_getReportList():
    try:
        initDB(testDB)
    except:
        resetDB()
    print('Test Get Report List...')

    rid = None

    #------------#
    # Unit Tests #
    #------------#

    print('\tNo reports...')
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
    l = getReportList(b'user')
    assert isinstance(l, list)
    assert len(l) == 0
    print('\tPass\n')

    print('\tOne Report...')
    with db_session:
        Account(username=b'user2', password=hashPassword(b'pass'))
        r = Report(owner=Account[b'user2'], isAnalysisDone=True)
        commit()
        rid = r.id
    l = getReportList(b'user2')
    assert isinstance(l, list)
    assert len(l) == 1
    assert l[0] == rid
    print('\tPass\n')

    print('\tMany Reports...')
    with db_session:
        Account(username=b'user3', password=hashPassword(b'pass'))
        for _ in range(1000):
            Report(owner=Account[b'user3'], isAnalysisDone=True)
    l = getReportList(b'user3')
    assert isinstance(l, list)
    assert len(l) == 1000
    assert len(set(l)) == 1000 # Converting to set as an easy check for duplicates
    print('\tPass\n')

    print('\tBad Username...')
    l = getReportList(b'Fake')
    assert isinstance(l, list)
    assert len(l) == 0
    print('\tPass\n')

def test_getReport():
    try:
        dbInit(testDB)
    except:
        resetDB()
    print('Test Get Report...')

    rid = None

    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
        Report(owner=Account[b'user'], isAnalysisDone=True)
        r = Report(owner=Account[b'user'], isAnalysisDone=True)
        commit()
        rid = r.id

    #------------#
    # Unit Tests #
    #------------#

    print('\tTest normal operation...')
    r = getReport(rid)
    assert isinstance(r, Report)
    assert r.id == rid
    print('\tPass\n')

    print('\tTest bad report id...')
    assert getReport(1000) is None
    print('\tPass\n')

def test_deleteReport():
    try:
        dbInit(testDB)
    except:
        resetDB()
    print('Test Delete Report...')

    rid = None

    #------------#
    # Unit Tests #
    #------------#

    print('\tTest normal operation...')
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
        r = Report(owner=Account[b'user'], isAnalysisDone=True)
        commit()
        rid = r.id
    assert deleteReport(rid)
    with db_session:
        assert not Report.get(id=rid)
    print('\tPass\n')

    print('\tTest bad report id...')
    assert not deleteReport(1000)
    print('\tPass\n')


def test_deleteAllReports():
    try:
        dbInit(testDB)
    except:
        resetDB()

    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
        Account(username=b'user2', password=hashPassword(b'pass'))

    print('Test Delete All Reports...')

    #------------#
    # Unit Tests #
    #------------#
    
    print('\tDelete One...')
    with db_session:
        Report(owner=Account[b'user'], isAnalysisDone=True)
    deleteAllReports(b'user')
    with db_session:
        assert len(Account[b'user'].reports) == 0
        assert count(x for x in Report) == 0
    print('\tPass\n')

    print('\tDelete Many...')
    with db_session:
        for _ in range(1000):
            Report(owner=Account[b'user'], isAnalysisDone=True)
    deleteAllReports(b'user')
    with db_session:
        assert len(Account[b'user'].reports) == 0
        assert count(x for x in Report) == 0
    print('\tPass\n')

    print('\tNothing to delete...')
    deleteAllReports(b'user')
    with db_session:
        assert len(Account[b'user'].reports) == 0
        assert count(x for x in Report) == 0
    print('\tPass\n')

    print('\tDelete for one user when other users have reports...')
    with db_session:
        Report(owner=Account[b'user'], isAnalysisDone=True)
        Report(owner=Account[b'user'], isAnalysisDone=True)
        Report(owner=Account[b'user2'], isAnalysisDone=True)
    deleteAllReports(b'user')
    with db_session:
        assert len(Account[b'user'].reports) == 0
        assert count(x for x in Report) == 1
    print('\tPass\n')

    print('\tBad username')
    n = 0
    with db_session:
        Report(owner=Account[b'user'], isAnalysisDone=True)
        n = count(x for x in Report)
    deleteAllReports(b'Fake')
    with db_session:
        assert count(x for x in Report) == n # No change should occur
    print('\tPass\n')

def test_deleteAccount():
    try:
        dbInit(testDB)
    except:
        resetDB()
    print('Test Delete Account...')

    #------------#
    # Unit Tests #
    #------------#

    print('\tTest empty account...')
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
    assert deleteAccount(b'user')
    with db_session:
        assert not Account.get(username=b'user')
        assert count(x for x in Account) == 0
    print('\tPass\n')

    print('\tTest account with reports...')
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
        Report(owner=Account[b'user'], isAnalysisDone=True)
        Report(owner=Account[b'user'], isAnalysisDone=True)
    assert deleteAccount(b'user')
    with db_session:
        assert not Account.get(username=b'user')
        assert count(x for x in Account) == 0
        assert count(x for x in Report) == 0
    print('\tPass\n')

    print('\tTest delete account when other accounts exist...')
    with db_session:
        Account(username=b'user', password=hashPassword(b'pass'))
        Account(username=b'user2', password=hashPassword(b'pass'))
        Report(owner=Account[b'user'], isAnalysisDone=True)
        Report(owner=Account[b'user'], isAnalysisDone=True)
        Report(owner=Account[b'user2'], isAnalysisDone=True)
    assert deleteAccount(b'user')
    with db_session:
        assert not Account.get(username=b'user')
        assert count(x for x in Account) == 1
        assert count(x for x in Report) == 1
    print('\tPass\n')



def test_db():
    test_dbInit()
    test_newAccount()
    test_login()
    test_checkToken()
    test_logout()
    test_changePassword()
    test_newPassword()
    test_newReport()
    test_updateReport()
    test_getReportList()
    test_getReport()
    test_deleteReport()
    test_deleteAllReports()
    test_deleteAccount()

if __name__ == '__main__':
    test_db()
