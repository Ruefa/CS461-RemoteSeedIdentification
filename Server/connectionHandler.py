import sys
import os
import pathlib
import socket
import queue
import threading

from pony import orm

import error
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

def sendReport(conn, report):
    msg = error.Success + b'|' + report.results.encode() + b'|'
    length = len(msg) + os.path.getsize(str(report.resultsImg))
    conn.sendall(length.to_bytes(4, byteorder='big') + msg)
    with open(str(report.resultsImg), 'rb') as f:
        conn.sendfile(f)

def newAccount(credentials):
    if b':' not in credentials:
        return (error.InvalidMsg,)
    username, password = credentials.split(b':')

    try:
        # Account creation succeeded
        if db.newAccount(username, password):
            return (error.Success,)
    except:
        return (error.DBError,)

    # Account creation failed
    return (error.DuplicateUser,)

def login(credentials):
    if b':' not in credentials:
        return (error.InvalidMsg,)
    username, password = credentials.split(b':')

    try:
        auth = db.login(username, password)
    except:
        return (error.DBError,)

    # Successful login
    if auth:
        threadData.currentUser = username
        return (error.Success, auth)
    # Failed Login
    threadData.currentUser = None
    return (error.BadCredentials,)

def checkAuth(auth):
    if len(auth) < tokenLen:
        return (error.InvalidMsg,)
    username, token = auth[:-db.tokenLen], auth[-db.tokenLen:]

    try:
        if db.checkToken(username, token):
            threadData.currentUser = username
            return (error.Success,)
    except:
        return (error.DBError,)

    threadData.currentUser = None
    return (error.BadToken,)

def runAnalysis(conn, length):
    user = threadData.currentUser
    if not user:
        return (error.Unauthorized,)

    # Add a new blank report to the DB and get its ID
    try: 
        reportID = db.newReport(user)
    except:
        return (error.DBError,)

    # Write the image to a file and store the path in the DB
    path = db.dbDirectory / user.decode() / str(reportID) / 'sample.jpg'
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), 'wb') as f:
        readMsgToFile(conn, length, f)

    try:
        db.updateReport(reportID, sourceImg=str(path))
    except:
        return (error.DBError,)

    jobQueue.put((reportID, path))
    
    return (error.Success, str(reportID).encode())
    
def getReportList(_):
    user = threadData.currentUser
    if not user:
        return (error.Unauthorized,)

    try:
        l = [str(x) for x in db.getReportList(user)]
    except:
        return (error.DBError,)

    return (error.Success,'|'.join(l).encode())

#TODO Handle incomplete report
def getReport(report):
    user = threadData.currentUser
    if not user:
        return (error.Unauthorized,)

    try:
        reportID = int(report)
    except:
        return (error.InvalidMsg,)
    
    try:
        r = db.getReport(reportID)
    except:
        return (error.DBError,)

    if r:
        return (error.Success, r)
    return (error.InvalidReportID,)

def deleteReport(report):
    user = threadData.currentUser
    if not user:
        return (error.Unauthorized,)

    try:
        reportID = int(report)
    except:
        return (error.InvalidMsg,)

    try:
        r = db.deleteReport(user, reportID)
    except:
        return (error.DBError,)

    if r:
        return (error.Success,)
    return (error.InvalidReportID,)

def deleteAllReports(_):
    user = threadData.currentUser
    if not user:
        return (error.Unauthorized,)

    try:
        if db.deleteAllReports(user):
            return (error.Success,)
    except:
        return (error.DBError,)
    return bytes([0])

def deleteAccount(_):
    user = threadData.currentUser
    if not user:
        return (error.Unauthorized,)

    try:
        if db.deleteAccount(user):
            threadData.currentUser = None
            return (error.Success,)
    except:
        return (error.DBError,)
    return (error.Failure,)

def logout(_):
    user = threadData.currentUser
    if not user:
        return (error.Unauthorized,)

    try:
        if db.logout(user):
            threadData.currentUser = None
            return (error.Success,)
    except:
        return (error.DBError,)
    return (error.Failure,)

def changePassword(passwords):
    if b'|' not in passwords:
        return (error.InvalidMsg,)
    oldPass, newPass = passwords.split(b'|')

    user = threadData.currentUser
    if not user:
        return (error.Unauthorized,)

    try:
        if db.login(user, oldPass, newToken = False):
            db.changePassword(user, newPass)
            return (error.Success,)
        # Old Password was bad
        return (error.BadCredentials,)
    except:
        return (error.DBError,)

def forgotPassword(user):
    password = db.newPassword(user)
    #TODO Email new password
    return (error.Success,)


dispatch = { 1:   newAccount,
             2:   login,
             3:   checkAuth,
             4:   changePassword,
             5:   forgotPassword,
             6:   deleteAccount,
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
        elif msgType == 102:
            msg = readMsg(conn, length)
            response = getReport(msg)
            if response[0] == error.Success:
                sendReport(conn, response[1])
                continue
        else:
            msg = readMsg(conn, length)
            response = dispatch[msgType](msg)
        print(type(msg), response)
        sendMsg(conn, b'|'.join(response))

        msgType, length = readMsgHeader(conn)

    #conn.shutdown(socket.SHUT_RDWR)
    conn.close()
