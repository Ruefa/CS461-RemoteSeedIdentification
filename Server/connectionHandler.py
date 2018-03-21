import sys
import pathlib
import socket

from pony import orm

import db
sys.path.append('/home/nvidia/RemoteSeed/CS461-RemoteSeedIdentification/Classifier')
from sample_analysis import run_analysis

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

# Sends a bytes object over the connection
def sendData(conn, data):
    #TODO May be more robust to use send in a loop? Investigate further
    conn.sendall(data)

# Makes a new login
# Returns True on success, else False
def newAccount(credentials):
    username, password = credentials.split(b'@')
    return db.newAccount(username, password)

# Takes credentials in the format username@password.
# Returns a login session token if credentials are valid, otherwise None
def login(credentials):
    username, password = credentials.split(b'@')
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

    f = open(str(path / 'sample.jpg'), 'wb')
    f.write(img)
    f.close()

    results = run_analysis('sample.jpg', str(path))

    db.addReportResults(user, reportID, results)
    
    return reportID, results.encode()
    
def getReportList(user):
    #TODO Figure out a format for this. Could just use delimiters or
    #     could use xml or JSON, ect.
    return db.getReportList(user)

# Get the report stored in the data base with id 'report' under username 'user'
def getReport(user, report):
    return db.getReport(user, int.from_bytes(report, 'big'))[0]

def sendReportImg(conn, user, reportID, img='result.png'):
    msg = b''
    path = pathlib.Path('/home/nvidia/RemoteSeed/DB/users/{}/{}/{}'.format(user.decode(), reportID, img))
    f = open(str(path), 'rb')
    buf = f.read(4096)
    while buf:
        msg += buf
        buf = f.read(4096)
    f.close
    sendData(conn, msg)


def handleConn(conn):
    msg = readMsg(conn)
    while (msg):
        msgType, msg = msg[0], bytes(msg[1:])

        # ASCII letters alphabetically from 'a' are used to indicate message type.
        # Using ASCII is convenient for pythons representation of received data, 
        # and I can't think of meaningful single character codes for every action
        if msgType == 97: # Make Login
            if newAccount(msg):
                conn.send(bytes([1])) # Valid login
            else:
                conn.send(bytes([0])) # Invalid login
        elif msgType == 98: # Login Info
            auth = login(msg)
            if auth:
                conn.send(auth) # Valid login
            else:
                conn.send(bytes([0])) # Invalid login
        elif msgType == 99: # Request new analysis
            auth, data = msg.split(b'|', maxsplit=1)
            user = checkAuth(auth)
            if user:
                #TODO Add some error checking here
                reportID, report = runAnalysis(data, user)
                sendData(conn, report + b'|')
                sendReportImg(conn, user, reportID)
            else:
                conn.send(bytes([0])) # Invalid login
        elif msgType == 100: # Request list of reports for certain username
            user = checkAuth(msg)
            if user:
                #TODO send report ids instead of results?
                data = '|'.join([str(x) for x in getReportList(user)])
                sendData(conn, data.encode())
            else:
                conn.send(bytes([0])) # Invalid login
        elif msgType == 101: # Request a specific report
            auth, data = msg.split(b'|', maxsplit=1)
            user = checkAuth(auth)
            if user:
                reportID = int.from_bytes(data, 'big')
                report = getReport(user, data)
                sendData(conn, report.encode()+b'|')
                sendReportImg(conn, user, reportID)
            else:
                conn.send(bytes([0])) # Invalid login
        elif msgType == 122: # Logout
            db.logout(checkAuth(msg))

        msg = readMsg(conn)

    conn.close()
