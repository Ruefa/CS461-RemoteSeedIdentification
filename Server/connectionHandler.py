import sys
import pathlib
import socket
import queue
import threading 

from pony import orm

import db

jobQueue = queue.Queue()
threadData = threading.local()
threadData.currentUser = None


# Read the first 4 bytes from the connection to determine message size, then read
# the entire message.
def readMsg(conn, chunkSize = 4096):
    # Read the message length first
    sizeBytes = conn.recv(4)
    if not sizeBytes: # Connection closed
        return None

    while len(sizeBytes) < 4:
        sizeBytes += conn.recv(4 - len(sizeBytes))

    remaining = int.from_bytes(sizeBytes, byteorder='big')
    buf = bytearray()

    # Get data from the connection until the entire message is read
    while remaining:
        chunk = conn.recv(min(chunkSize, remaining))
        remaining -= len(chunk)
        buf += chunk

    return buf

def sendMsg(conn, msg):
    msg = len(msg).to_bytes(4, byteorder='big') + msg
    conn.sendall(msg)

def sendReport(user, reportID, results, img='result.png'):
    path = pathlib.Path('/home/nvidia/RemoteSeed/DB/users/{}/{}/{}'.format(user.decode(), reportID, img))

    buf = bytearray()
    buf += results.encode()
    buf += b'|'

    with open(str(path), 'rb') as f:
        buf += f.read()
        
    return buf


def newAccount(credentials):
    username, password = credentials.split(b':')
    if db.newAccount(username, password):
        return bytes([1])
    return bytes([0])

def login(credentials):
    username, password = credentials.split(b':')
    auth = db.login(username, password)
    if auth:
        threadData.currentUser = username
        return auth # Valid login
    threadData.currentUser = None
    return bytes([0]) # Invalid login

def checkAuth(auth):
    username = auth[:-db.tokenLen]
    token = auth[-db.tokenLen:]
    if db.checkToken(username, token):
        threadData.currentUser = username
        return bytes([1])
    threadData.currentUser = None
    return bytes([0])

def runAnalysis(img):
    user = threadData.currentUser
    if user:
        reportID = db.newReport(user)

        path = pathlib.Path('/home/nvidia/RemoteSeed/DB/users/{}/{}'.format(user.decode(), reportID))
        path.mkdir(parents=True, exist_ok=True)

        with open(str(path / 'sample.jpg'), 'wb') as f:
            f.write(img)
        
        jobQueue.put(('sample.jpg', str(path), user, reportID))
        
        return str(reportID).encode()
    return bytes([0])
    
def getReportList(_):
    #TODO Figure out a format for this. Could just use delimiters or
    #     could use xml or JSON, ect.
    user = threadData.currentUser
    if user:
        return '|'.join([str(x) for x in db.getReportList(user)]).encode()
    return bytes([0])

def getReport(report):
    user = threadData.currentUser
    if user:
        reportID = int(report)
        r = db.getReport(user, reportID)[0]
        if r:
            return sendReport(user, reportID, r)
    return bytes([0])

def deleteReport(report):
    user = threadData.currentUser
    if user:
        reportID = int(report)
        r = db.deleteReport(user, reportID)
        if r:
            return bytes([1])
    return bytes([0])

def deleteAllReports(_):
    user = threadData.currentUser
    if user and db.deleteAllReports(user):
        return bytes([1])
    return bytes([0])

def deleteAccount(_):
    user = threadData.currentUser
    if user and db.deleteAccount(user):
        return bytes([1])
    return bytes([0])

def logout(_):
    user = threadData.currentUser
    if user and db.logout(user):
        return bytes([1])
    return bytes([0])

def changePassword(passwords):
    oldPass, newPass = passwords.split(b':')
    user = threadData.currentUser
    if user and db.login(user, oldPass, newToken = False):
        db.changePassword(user, newPass)
        return bytes([1])
    return bytes([0])

def forgotPassword(user):
    password = db.newPassword(user)
    #TODO Email new password
    return bytes([1])


dispatch = { 97:  newAccount,
             98:  login,
             99:  runAnalysis,
             100: getReportList,
             101: getReport,
             102: deleteReport,
             103: deleteAllReports,
             104: deleteAccount,
             105: changePassword,
             106: forgotPassword,
             122: logout
           }
    

def handleConn(conn):
    msg = readMsg(conn)
    while (msg):
        msgType, msg = msg[0], bytes(msg[1:])
        response = dispatch[msgType](msg)
        sendMsg(conn, response)

        msg = readMsg(conn)

    #conn.shutdown(socket.SHUT_RDWR)
    conn.close()
