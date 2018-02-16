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

    #TODO Do something to check credentials against DB
    if True:
        return 'user'
    else:
        return None

def runAnalysis(img, user):
    #TODO Link in with Ethans work
    #     Generate and return results
    #     Store them in DB
    return b'Analysis run (this is a placeholder)'

def getReportList(user):
    #TODO More database stuff
    #TODO Figure out a format for this. Could just use delimiters or
    #     could use xml or JSON, ect.
    return [b'Test Report 1', b'Test Report 2']

# Get the report stored in the data base with id 'report' under username 'user'
def getReport(user, report):
    #TODO DB
    return b'Test Report'

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
        credentials, data = data.split(b'|')
        user = checkLogin(credentials)
        if user:
            #TODO Add some error checking here
            report = runAnalysis(data, user)
        else:
            conn.send(bytes([0])) # Invalid login
        sendData(conn, report)
    elif msgType == b'd': # Request list of reports for certain username
        user = checkLogin(readData(conn))
        if user:
            data = b'|'.join(getReportList(user))
            conn.sendData(conn, data)
        else:
            conn.send(bytes([0])) # Invalid login
    elif msgType == b'e': # Request a specific report
        data = readData(conn)
        credentials, data = data.split(b'|')
        user = checkLogin(credentials)
        if user:
            report = getReport(user, data)
        else:
            conn.send(bytes([0])) # Invalid login
        sendData(conn, report)

    conn.close()
