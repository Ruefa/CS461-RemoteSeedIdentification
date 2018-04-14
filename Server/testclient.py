import socket, ssl
import time
import sys

# These are not extensive unit tests, just preliminary testing

# This code is awful and will be replaced with real tests eventually

port = 5777
address = '73.11.102.15'

useSsl = False
context = ssl.create_default_context(cafile='cert.pem')


token = b''
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
if useSsl:
    s = context.wrap_socket(s, server_hostname='73.11.102.15')

def connect():
    s.connect((address, port))

def disconnect():
    s.close()

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

def testMakeAccount(username, password):
    msg = b'a' + username + b':' + password
    print('Message:', msg)
    sendMsg(s, msg)

    print('Result:', readMsg(s).hex())

def testLogin(username, password):
    msg = b'b' + username + b':' + password
    print('Message:', msg)
    sendMsg(s, msg)

    token = readMsg(s)

    print('Result:', token.hex())

def testRunAnalysis(username, path):
    f = open(path, 'rb')
    msg = b'c'
    
    buf = f.read(4096)
    while buf:
        msg += buf
        buf = f.read(4096)
    f.close()

    sendMsg(s, msg) 

    results = readMsg(s)
    
    print('Results:', results.decode())

def testGetReportList(username):
    msg = b'd'
    print('Message:', msg)
    sendMsg(s, msg)

    print('Results:', readMsg(s))

def testGetReport(username, reportID):
    msg = b'e' + str(reportID).encode()
    print('Message:', msg)
    sendMsg(s, msg)

    response = readMsg(s)
    if len(response) > 2:
        results, img = response.split(b'|', maxsplit=1);
        f = open('results.png', 'wb')
        f.write(img)
        print('Results:', results.decode())
    else:
        print('Results', response.hex())

def testLogout(username):
    msg = b'z'
    print('Message:', msg)
    sendMsg(s, msg)

    print('Logged Out')



if __name__ == "__main__":
    connect()
    testMakeAccount(b'UserName', b'Password')
    testLogin(b'UserName', b'Password')
    testRunAnalysis(b'UserName', b'test.JPG') # Only works on my local machine (obviously)
    testGetReportList(b'UserName')
    testGetReport(b'UserName', 1)
    testLogout(b'UserName')
    testGetReportList(b'UserName')
    disconnect()




