import socket, ssl
import threading
import pathlib
import time
import sys
import os
import datetime
sys.path.append(os.path.abspath('..'))

from connectionHandler import *
import connectionHandler
import db
import error

port = 5779
address = 'localhost'

def test_readMsgHeader():
    print('Test readMsgHeader...')
    # setup server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    # Set up client socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((address, port))

    conn, _ = server.accept()

    # Read and discard l bytes from conn
    def purgeData(l, conn):
        count = 0
        while count < l:
            count += len(conn.recv(l-count))

    #------------#
    # Unit Tests #
    #------------#

    print('\tTest normal operation...')
    msg = bytes([1]) + b'Test'
    msg = len(msg).to_bytes(4, byteorder='big') + msg
    s.sendall(msg)
    t, l = readMsgHeader(conn)
    assert t == 1
    assert l == 4
    print('\tPass\n')
    
    purgeData(l, conn)

    print('\tTest length prefix arriving in multiple packets...')
    msg = bytes([1]) + b'Test'
    msg = len(msg).to_bytes(4, byteorder='big') + msg
    def sendSlow(s):
        for i in range(5):
            s.sendall(msg[i:i+1])
            time.sleep(.25)
        s.sendall(msg[5:])
    th = threading.Thread(target = sendSlow, args=(s,))
    th.start()
    t, l = readMsgHeader(conn)
    th.join()
    assert t == 1
    assert l == 4
    print('\tPass\n')

    purgeData(l, conn)

    print('\tTest disconnected socket...')
    s.shutdown(socket.SHUT_RDWR)
    s.close()
    t, l = readMsgHeader(conn)
    assert not t
    assert l  == 0
    print('\tPass\n')

    conn.close()
    time.sleep(.5)

def test_readMsg():
    print('Test readMsg...')
    # setup server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    # Set up client socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((address, port))

    conn, _ = server.accept()

    print('\tTesting normal operation...')
    msg = b'test'
    l = len(msg)
    s.sendall(msg)
    result = readMsg(conn, l)
    assert result == msg
    print('\tPass\n')

    # This tests a message being split up because of TCP issues as well
    print('\tTesting length bigger than chunk size...')
    msg = bytes([23 for _ in range(1000)])
    l = len(msg)
    s.sendall(msg)
    result = readMsg(conn, l, chunkSize=256)
    assert result == msg
    print('\tPass\n')

    s.shutdown(socket.SHUT_RDWR)
    s.close()
    conn.close()
    time.sleep(.5)

def test_readMsgToFile():
    print('Test readMsgToFile...')
    # setup server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    # Set up client socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((address, port))

    conn, _ = server.accept()

    fname = 'test'


    print('\tTesting normal operation...')
    msg = b'test'
    l = len(msg)
    s.sendall(msg)
    with open(fname, 'wb') as f:
        readMsgToFile(conn, l, f)
    with open(fname, 'rb') as f:
        assert f.read() == msg
    print('\tPass\n')

    # This tests a message being split up because of TCP issues as well
    print('\tTesting length bigger than chunk size...')
    msg = bytes([23 for _ in range(1000)])
    l = len(msg)
    s.sendall(msg)
    with open(fname, 'wb') as f:
        readMsgToFile(conn, l, f, chunkSize=256)
    with open(fname, 'rb') as f:
        assert f.read() == msg
    print('\tPass\n')

    s.shutdown(socket.SHUT_RDWR)
    s.close()
    conn.close()
    os.remove(fname) # Cleanup file
    time.sleep(.5)

def test_sendMsg():
    print('Test sendMsg...')
    # setup server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    # Set up client socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((address, port))

    conn, _ = server.accept()

    msg = b'This is but a test'

    sendMsg(conn, msg)
    # Not using a recv loop, so may fail if there is a lot of congestion on network
    assert s.recv(1024) == len(msg).to_bytes(4, byteorder='big') + msg
    print('Pass\n')

    s.shutdown(socket.SHUT_RDWR)
    s.close()
    conn.close()
    time.sleep(.5)

def test_sendReport():
    print('Test sendReport...')
    # setup server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('', port))
    server.listen(5)
    # Set up client socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((address, port))

    ftest = 'test'
    r = None

    conn, _ = server.accept()
    with open(ftest, 'wb') as f:
        f.write(b'These are results in a file. If this were real this would be an image file.')
    class ReportSim:
        results = 'results'
        resultsImg = ftest

    r = ReportSim()

    sendReport(conn, r)
    
    # Not using a recv loop, so may fail if there is a lot of congestion on network
    result = s.recv(1024)
    assert int.from_bytes(result[:4], byteorder='big') == len(result[4:])
    results = result.split(b'|')
    assert len(results) == 3
    assert results[0][4:] == error.Success
    assert results[1].decode() == r.results
    assert results[2] == b'These are results in a file. If this were real this would be an image file.'
    print('Pass\n')

    s.shutdown(socket.SHUT_RDWR)
    s.close()
    conn.close()
    os.remove(fname) # Cleanup file

def test_newAccount():
    print('Test newAccount...')
    
    print('\tTest invalid message...')
    result = newAccount(b'asdasdasdasda')
    assert len(result) == 1
    assert result[0] == error.InvalidMsg
    print('\tPass\n')

    print('\tTest DB error...')
    def throwException(u, p):
        assert False
    db.newAccount = throwException
    result = newAccount(b'user:pass')
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTest normal operation...')
    def returnTrue(u, p):
        return True
    db.newAccount = returnTrue
    result = newAccount(b'user:pass')
    assert len(result) == 1
    assert result[0] == error.Success
    print('\tPass\n')

    print('\tTest failure (duplicate username)...')
    def returnFalse(u, p):
        return False
    db.newAccount = returnFalse
    result = newAccount(b'user:pass')
    assert len(result) == 1
    assert result[0] == error.DuplicateUser
    print('\tPass\n')

def test_login():
    print('Test login...')
    
    print('\tTest invalid message...')
    result = login(b'asdasdasdasda')
    assert len(result) == 1
    assert result[0] == error.InvalidMsg
    print('\tPass\n')

    print('\tTest DB error...')
    def throwException(u, p):
        assert False
    db.login = throwException
    result = login(b'user:pass')
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTest normal operation...')
    def returnAuth(u, p):
        return b'Fake auth string'
    db.login = returnAuth
    result = login(b'user:pass')
    assert len(result) == 2
    assert result[0] == error.Success
    assert result[1] == b'Fake auth string'
    assert threadData.currentUser == b'user'
    print('\tPass\n')

    print('\tTest failure (Bad username/pass)...')
    def returnNone(u, p):
        return None
    db.login = returnNone
    result = login(b'user:pass')
    assert len(result) == 1
    assert result[0] == error.BadCredentials
    print('\tPass\n')

def test_checkAuth():
    print('Testing checkAuth...')
    auth = b'user' + os.urandom(db.tokenLen)

    print('\tTesting invalid message...')
    result = checkAuth(b'User12321')
    assert len(result) == 1
    assert result[0] == error.InvalidMsg
    print('\tPass\n')

    print('\tTesting DB error...')
    def throwException(u, a):
        assert False
    db.checkToken = throwException
    result = checkAuth(auth)
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting normal operation...')
    def returnTrue(u, a):
        return True
    db.checkToken = returnTrue
    result = checkAuth(auth)
    assert len(result) == 1
    assert result[0] == error.Success
    assert threadData.currentUser == b'user'
    print('\tPass\n')

    print('\tTest failure (bad auth)...')
    def returnFalse(u, a):
        return False
    db.checkToken = returnFalse
    result = checkAuth(auth)
    assert len(result) == 1
    assert result[0] == error.BadToken
    print('\tPass\n')

def test_runAnalysis():
    print('Testing runAnalysis...')

    print('\tTesting not logged in...')
    threadData.currentUser = None
    result = runAnalysis(1, 1)
    assert len(result) == 1
    assert result[0] == error.Unauthorized
    print('\tPass\n')

    print('\tTesting DB error...')
    threadData.currentUser = b'user'
    def throwException(_):
        assert False
    db.newReport = throwException
    result = runAnalysis(1, 1)
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting normal operation...')
    p = pathlib.Path('.')
    db.dbDirectory = p
    def returnId(_):
        return 1
    db.newReport=returnId

    def validateReportUpdate(id, sourceImg=''):
        assert id == 1
        assert sourceImg == str(p / 'user' / '1' / 'sample.jpg')
    db.updateReport=validateReportUpdate

    def writeToFile(c, l, f):
        f.write(b'test')
    connectionHandler.readMsgToFile = writeToFile
    result = runAnalysis(1, 1)
    assert len(result) == 2
    assert result[0] == error.Success
    assert result[1] == b'1'
    with open(str(p / 'user' / '1' / 'sample.jpg'), 'rb') as f:
        assert f.read() == b'test'
    job = jobQueue.get()
    assert job[0] == 1
    assert job[1] == p / 'user' / '1' / 'sample.jpg'
    print('\tPass\n')

    os.remove(str(job[1]))
    os.rmdir(str(job[1].parent))
    os.rmdir(str(job[1].parent.parent))

def test_getReportList():
    print('Testing get report list...')
    print('\tTesting not logged in...')
    threadData.currentUser = None
    result = getReportList(1)
    assert len(result) == 1
    assert result[0] == error.Unauthorized
    print('\tPass\n')

    print('\tTesting DB error...')
    threadData.currentUser = b'user'
    def throwException(_):
        assert False
    db.getReportList = throwException
    result = getReportList(1)
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting one report...')
    class ReportSim:
        id = 0
        datetime = datetime.datetime.today()
    def reportListTester(_):
        r = ReportSim()
        r.id = 1
        return [r]
    db.getReportList = reportListTester
    result = getReportList(1)
    assert len(result) == 2
    assert result[0] == error.Success
    assert result[1].split(b'@')[0] == b'1'
    print('\tPass\n')

    print('\tTesting multiple report...')
    class ReportSim:
        id = 0
        datetime = datetime.datetime.today()
    def reportListTester(_):
        l = [ReportSim() for _ in range(5)]
        for i in range(5):
            l[i].id = i
        return l
    db.getReportList = reportListTester
    result = getReportList(1)
    assert len(result) == 2
    assert result[0] == error.Success
    assert len(result[1].split(b'|')) == 5
    print('\tPass\n')

def test_getReport():
    print('testing get report...')
    print('\tTesting not logged in...')
    threadData.currentUser = None
    result = getReport(1)
    assert len(result) == 1
    assert result[0] == error.Unauthorized
    print('\tPass\n')

    print('\tTesting invalid message...')
    threadData.currentUser = b'user'
    result = getReport('a')
    assert len(result) == 1
    assert result[0] == error.InvalidMsg
    print('\tPass\n')

    print('\tTesting DB error...')
    threadData.currentUser = b'user'
    def throwException(_):
        assert False
    db.getReport = throwException
    result = getReport(1)
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting normal operation...')
    threadData.currentUser = b'user'
    class ReportSim:
        id = 1
        isAnalysisDone = True
    r = ReportSim() 
    def returnReport(_):
        return r
    db.getReport = returnReport
    result = getReport(1)
    assert len(result) == 2
    assert result[0] == error.Success
    assert result[1] == r
    print('\tPass\n')

    print('\tTesting report not finished...')
    threadData.currentUser = b'user'
    class ReportSim:
        id = 1
        isAnalysisDone = False
    r = ReportSim() 
    def returnReport(_):
        return r
    db.getReport = returnReport
    result = getReport(1)
    assert len(result) == 1
    assert result[0] == error.ReportInProgress
    print('\tPass\n')

    print('\tTesting bad report id...')
    threadData.currentUser = b'user'
    def returnNone(_):
        return None
    db.getReport = returnNone
    result = getReport(1)
    assert len(result) == 1
    assert result[0] == error.InvalidReportID
    print('\tPass\n')

def test_deleteReport():
    print('Testing delete report...')
    print('\tTesting not logged in...')
    threadData.currentUser = None
    result = deleteReport(1)
    assert len(result) == 1
    assert result[0] == error.Unauthorized
    print('\tPass\n')

    print('\tTesting invalid message...')
    threadData.currentUser = b'user'
    result = deleteReport('a')
    assert len(result) == 1
    assert result[0] == error.InvalidMsg
    print('\tPass\n')

    print('\tTesting DB error...')
    threadData.currentUser = b'user'
    def throwException(_):
        assert False
    db.deleteReport = throwException
    result = deleteReport(1)
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting normal operation...')
    threadData.currentUser = b'user'
    def returnTrue(u, r):
        return True
    db.deleteReport = returnTrue
    result = deleteReport(1)
    print(result)
    assert len(result) == 1
    assert result[0] == error.Success
    print('\tPass\n')

    print('\tTesting bad report id...')
    threadData.currentUser = b'user'
    def returnFalse(u, r):
        return False
    db.deleteReport = returnFalse
    result = deleteReport(1)
    assert len(result) == 1
    assert result[0] == error.InvalidReportID
    print('\tPass\n')

def test_deleteAllReports():
    print('Testing delete all report...')
    print('\tTesting not logged in...')
    threadData.currentUser = None
    result = deleteAllReports(1)
    assert len(result) == 1
    assert result[0] == error.Unauthorized
    print('\tPass\n')

    print('\tTesting DB error...')
    threadData.currentUser = b'user'
    def throwException(_):
        assert False
    db.deleteAllReports = throwException
    result = deleteAllReports(1)
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting normal operation...')
    threadData.currentUser = b'user'
    def returnTrue(_):
        return True
    db.deleteAllReports = returnTrue
    result = deleteAllReports(1)
    assert len(result) == 1
    assert result[0] == error.Success
    print('\tPass\n')

    print('\tTesting failure...')
    threadData.currentUser = b'user'
    def returnFalse():
        return False
    db.deleteAllReports = returnFalse
    result = deleteAllReports(1)
    assert len(result) == 1
    assert result[0] == error.Failure
    print('\tPass\n')

def test_deleteAccount():
    print('Testing delete account...')
    print('\tTesting not logged in...')
    threadData.currentUser = None
    result = deleteAccount(1)
    assert len(result) == 1
    assert result[0] == error.Unauthorized
    print('\tPass\n')

    print('\tTesting DB error...')
    threadData.currentUser = b'user'
    def throwException(_):
        assert False
    db.deleteAccount = throwException
    result = deleteAccount(1)
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting normal operation...')
    threadData.currentUser = b'user'
    def returnTrue(_):
        return True
    db.deleteAccount = returnTrue
    result = deleteAccount(1)
    assert len(result) == 1
    assert result[0] == error.Success
    assert threadData.currentUser == None
    print('\tPass\n')

    print('\tTesting failure...')
    threadData.currentUser = b'user'
    def returnFalse(_):
        return False
    db.deleteAccount = returnFalse
    result = deleteAccount(1)
    assert len(result) == 1
    assert result[0] == error.Failure
    print('\tPass\n')

def test_logout():
    print('Testing delete account...')
    print('\tTesting not logged in...')
    threadData.currentUser = None
    result = logout(1)
    assert len(result) == 1
    assert result[0] == error.Unauthorized
    print('\tPass\n')

    print('\tTesting DB error...')
    threadData.currentUser = b'user'
    def throwException(_):
        assert False
    db.logout = throwException
    result = logout(1)
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting normal operation...')
    threadData.currentUser = b'user'
    def returnTrue(_):
        return True
    db.logout = returnTrue
    result = logout(1)
    assert len(result) == 1
    assert result[0] == error.Success
    assert threadData.currentUser == None
    print('\tPass\n')

    print('\tTesting failure...')
    threadData.currentUser = b'user'
    def returnFalse(_):
        return False
    db.logout = returnFalse
    result = logout(1)
    assert len(result) == 1
    assert result[0] == error.Failure
    print('\tPass\n')

def test_changePassword():
    print('Testing change password...')
    print('\tTesting Invalid message...')
    result = changePassword(b'asdasda')
    assert len(result) == 1
    assert result[0] == error.InvalidMsg
    print('\tPass\n')

    print('\tTesting not logged in...')
    threadData.currentUser = None
    result = changePassword(b'old|new')
    assert len(result) == 1
    assert result[0] == error.Unauthorized
    print('\tPass\n')

    print('\tTesting normal operation...')
    threadData.currentUser = b'user'
    threadData.currentUser = b'user'
    def returnTrue(u, p, newToken):
        return True
    db.login = returnTrue
    def doNothing(u, p):
        pass
    db.changePassword = doNothing
    result = changePassword(b'Old|New')
    assert len(result) == 1
    assert result[0] == error.Success
    print('\tPass\n')

    print('\tTesting DB error...')
    threadData.currentUser = b'user'
    def returnTrue(u, p, newToken):
        return True
    db.login = returnTrue
    def throwException(old, new):
        assert False
    db.changePassword = throwException
    result = changePassword(b'old|new')
    assert len(result) == 1
    assert result[0] == error.DBError
    print('\tPass\n')

    print('\tTesting bad password...')
    threadData.currentUser = b'user'
    def returnFalse(u, p, newToken):
        return False
    db.login = returnFalse
    result = changePassword(b'old|new')
    assert len(result) == 1
    assert result[0] == error.BadCredentials
    print('\tPass\n')




def test_connectionHandler():
    test_readMsgHeader()
    test_readMsg()
    test_readMsgToFile()
    test_sendMsg()
    test_sendReport()
    test_newAccount()
    test_login()
    test_checkAuth()
    test_runAnalysis()
    test_getReportList()
    test_getReport()
    test_deleteReport()
    test_deleteAccount
    test_logout()
    test_changePassword()


test_connectionHandler()

