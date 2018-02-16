import socket
import db
from pony import orm

# Reads a stream of data from the connection and returns it all as a bytes object
def readData(conn, chunkSize = 4096):
    chunks = []
    #TODO Look in to using recv_into instead of creating an array of bytes objects
    chunk = conn.recv(chunkSize)
    while chunk:
        chunks.append(chunk)
        chunk = conn.recv(chunkSize)
    return b''.join(chunks)

# Sends a bytes object over the connection
def sendData(conn, data):
    #TODO May be more robust to use send in a loop? Investigate further
    conn.sendall(data)

# Makes a new login
# Returns True on success, else False
def makeLogin(credentials):
    username, password = credentials.split(b'@')
    return db.makeLogin(username, password)

# Takes credentials in the format username@password and returns 
# a the username if they are correct or None if not
def checkLogin(credentials):
    username, password = credentials.split(b'@')
    if db.checkLogin(username, password):
        return username
    else:
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
    msgType = conn.recv(1)

    # ASCII letters alphabetically from 'a' are used to indicate message type.
    # Using ASCII is convenient for pythons representation of received data, 
    # and I can't think of meaningful single character codes for every action
    if msgType == b'a': # Make Login
        if makeLogin(readData(conn)):
            conn.send(bytes([1])) # Valid login
        else:
            conn.send(bytes([0])) # Invalid login
    elif msgType == b'b': # Login Info
        if checkLogin(readData(conn)):
            conn.send(bytes([1])) # Valid login
        else:
            conn.send(bytes([0])) # Invalid login
    elif msgType == b'c': # Request new analysis
        data = readData(conn)
        credentials, data = data.split(b'|', maxsplit=1)
        user = checkLogin(credentials)
        if user:
            #TODO Add some error checking here
            report = runAnalysis(data, user)
            sendData(conn, report)
        else:
            conn.send(bytes([0])) # Invalid login
    elif msgType == b'd': # Request list of reports for certain username
        user = checkLogin(readData(conn))
        if user:
            #TODO send report ids instead of results?
            data = b'|'.join(getReportList(user))
            sendData(conn, data)
        else:
            conn.send(bytes([0])) # Invalid login
    elif msgType == b'e': # Request a specific report
        data = readData(conn)
        credentials, data = data.split(b'|', maxsplit=1)
        user = checkLogin(credentials)
        #TODO Error checking (does report exist?)
        if user:
            report = getReport(user, data)
        else:
            conn.send(bytes([0])) # Invalid login
        sendData(conn, report)

    conn.close()
