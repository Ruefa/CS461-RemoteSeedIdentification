import sys
import pathlib
import socket
import queue

from pony import orm

import db

jobQueue = queue.Queue()

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

# Makes a new login
# Returns True on success, else False
def newAccount(credentials):
    username, password = credentials.split(b':')
    return db.newAccount(username, password)

# Takes credentials in the format username:password.
# Returns a login session token if credentials are valid, otherwise None
def login(credentials):
    username, password = credentials.split(b':')
    return db.login(username, password)

# Returns the username of the logged in user, or None if invalid token or username
def checkAuth(auth):
    username = auth[:-db.tokenLen]
    token = auth[-db.tokenLen:]
    if db.checkToken(username, token):
        return username
    return None

def runAnalysis(img, user):
    reportID = db.newReport(user)

    path = pathlib.Path('/home/nvidia/RemoteSeed/DB/users/{}/{}'.format(user.decode(), reportID))
    path.mkdir(parents=True, exist_ok=True)

    with open(str(path / 'sample.jpg'), 'wb') as f:
        f.write(img)
    
    jobQueue.put(('sample.jpg', str(path), user, reportID))
    
    return reportID
    
def getReportList(user):
    #TODO Figure out a format for this. Could just use delimiters or
    #     could use xml or JSON, ect.
    return db.getReportList(user)

# Get the report stored in the data base with id 'report' under username 'user'
def getReport(user, report):
    return db.getReport(user, int.from_bytes(report, 'big'))[0]

def deleteReport(user, reportID):
    return db.deleteReport(user, reportID)

def sendReport(conn, user, reportID, results, img='result.png'):
    path = pathlib.Path('/home/nvidia/RemoteSeed/DB/users/{}/{}/{}'.format(user.decode(), reportID, img))

    buf = bytearray()
    buf += results.encode()
    buf += b'|'

    with open(str(path), 'rb') as f:
        buf += f.read()
        
    sendMsg(conn, buf)


def handleConn(conn):
    msg = readMsg(conn)
    while (msg):
        msgType, msg = msg[0], bytes(msg[1:])

        # ASCII letters alphabetically from 'a' are used to indicate message type.
        # Using ASCII is convenient for pythons representation of received data, 
        # and I can't think of meaningful single character codes for every action
        if msgType == 97: # Make Login
            if newAccount(msg):
                sendMsg(conn, bytes([1])) # Valid login
            else:
                sendMsg(conn, bytes([0])) # Invalid login
        elif msgType == 98: # Login Info
            auth = login(msg)
            if auth:
                sendMsg(conn, auth) # Valid login
            else:
                sendMsg(conn, bytes([0])) # Invalid login
        elif msgType == 99: # Request new analysis
            auth, data = msg.split(b'|', maxsplit=1)
            user = checkAuth(auth)
            if user:
                #TODO Add some error checking here
                reportID = runAnalysis(data, user)
                sendMsg(conn, str(reportID).encode())
            else:
                sendMsg(conn, bytes([0])) # Invalid login
        elif msgType == 100: # Request list of reports for certain username
            user = checkAuth(msg)
            if user:
                #TODO send report ids instead of results?
                data = '|'.join([str(x) for x in getReportList(user)])
                sendMsg(conn, data.encode())
            else:
                sendMsg(conn, bytes([0])) # Invalid login
        elif msgType == 101: # Request a specific report
            auth, data = msg.split(b'|', maxsplit=1)
            user = checkAuth(auth)
            if user:
                reportID = int.from_bytes(data, 'big')
                report = getReport(user, data)
                print ('Report Contents:', report)
                if (report):
                    sendReport(conn, user, reportID, report)
                else:
                    sendMsg(conn, bytes([0]))
            else:
                sendMsg(conn, bytes([0])) # Invalid login
        elif msgType = 102: # Delete a report

        elif msgType == 122: # Logout
            db.logout(checkAuth(msg))

        msg = readMsg(conn)
    #conn.shutdown(socket.SHUT_RDWR)
    conn.close()
