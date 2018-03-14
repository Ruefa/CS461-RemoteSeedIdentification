import socket
import db

from pony import orm

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
    #TODO Link in with Ethans work
    #     Generate and return results
    
    # Temp code to write image to local directory, showing that 
    # it was received
    f = open('ReceivedImg.jpg', 'wb')
    f.write(img)
    

    results = b'Report Results Placeholder'
    db.addReport(user, results)
    
    return results
    
def getReportList(user):
    #TODO Figure out a format for this. Could just use delimiters or
    #     could use xml or JSON, ect.
    return db.getReportList(user)

# Get the report stored in the data base with id 'report' under username 'user'
def getReport(user, report):
    return db.getReport(user, int.from_bytes(report, 'big'))[0]

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
                report = runAnalysis(data, user)
                sendData(conn, report)
            else:
                conn.send(bytes([0])) # Invalid login
        elif msgType == 100: # Request list of reports for certain username
            user = checkAuth(msg)
            if user:
                #TODO send report ids instead of results?
                data = b'|'.join(getReportList(user))
                sendData(conn, data)
            else:
                conn.send(bytes([0])) # Invalid login
        elif msgType == 101: # Request a specific report
            auth, data = msg.split(b'|', maxsplit=1)
            user = checkAuth(auth)
            #TODO Error checking (does report exist?)
            if user:
                report = getReport(user, data)
                sendData(conn, report)
            else:
                conn.send(bytes([0])) # Invalid login
        elif msgType == 122: # Logout
            db.logout(checkAuth(msg))

        msg = readMsg(conn)

    conn.close()
