import sys
import os
import pathlib
import socket
import queue
import threading

from pony import orm

import db

jobQueue = queue.Queue()
threadData = threading.local()
threadData.currentUser = None

def readMsgHeader(conn):
    # Read the message length first
    sizeBytes = conn.recv(4)
    if not sizeBytes: # Connection closed
        return None, 0

    while len(sizeBytes) < 4:
        sizeBytes += conn.recv(4 - len(sizeBytes))

    length = int.from_bytes(sizeBytes, byteorder='big')
    msgType = ord(conn.recv(1))
    return msgType, length-1


def readMsg(conn, length, chunkSize = 4096):
    remaining = length
    buf = bytearray()

    # Get data from the connection until the entire message is read
    while remaining:
        chunk = conn.recv(min(chunkSize, remaining))
        remaining -= len(chunk)
        buf += chunk

    return bytes(buf)

def readMsgToFile(conn, length, file, chunkSize = 4096):
    remaining = length
    
    while remaining:
        chunk = conn.recv(min(chunkSize, remaining))
        remaining -= len(chunk)
        file.write(chunk)

def sendMsg(conn, msg):
    msg = len(msg).to_bytes(4, byteorder='big') + msg
    conn.sendall(msg)

def sendReport(conn, results, imgPath):
    msg = results.encode() + b'|'
    print('len', len(msg), '+', os.path.getsize(str(imgPath)))
    length = len(msg) + os.path.getsize(str(imgPath))
    conn.sendall(length.to_bytes(4, byteorder='big') + msg)
    print(str(imgPath))
    with open(str(imgPath), 'rb') as f:
        conn.sendfile(f)

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

def runAnalysis(conn, length):
    user = threadData.currentUser
    if user:
        reportID = db.newReport(user)
        path = db.dbDirectory / user.decode() / str(reportID) / 'sample.jpg'
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(path), 'wb') as f:
            readMsgToFile(conn, length, f)

        db.updateReport(reportID, sourceImg=str(path))

        jobQueue.put((reportID, path))
        
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
        r = db.getReport(reportID)
        if r and r.results:
            print (r.results)
            return r.results, pathlib.Path(r.resultsImg)
    return False

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


dispatch = { 1:   newAccount,
             2:   login,
             3:   changePassword,
             4:   forgotPassword,
             5:   deleteAccount,
             99:  logout,
             101: getReportList,
             103: deleteReport,
             104: deleteAllReports
           }
    
def handleConn(conn):
    msgType, length = readMsgHeader(conn)
    while msgType:
        # Run Analysis and Get Report are special cased to avoid moving image files around in memory
        if msgType == 100:
            response = runAnalysis(conn, length)
            sendMsg(conn, response)
        elif msgType == 102:
            msg = readMsg(conn, length)
            report = getReport(msg)
            sendReport(conn, *report)
        else:
            msg = readMsg(conn, length)
            response = dispatch[msgType](msg)
            sendMsg(conn, response)

        msgType, length = readMsgHeader(conn)

    #conn.shutdown(socket.SHUT_RDWR)
    conn.close()
