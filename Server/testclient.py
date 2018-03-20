import socket, ssl
import sys

# These are not extensive unit tests, just preliminary testing

# This code is awful and will be replaced with real tests eventually

port = 5777
address = '73.11.102.15'

useSsl = False
context = ssl.create_default_context(cafile='cert.pem')


token = b''

def testMakeAccount(username, password):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if useSsl:
            s = context.wrap_socket(s, server_hostname='73.11.102.15')
        s.connect((address, port))
        
        msg = b'a' + username + b'@' + password
        msg = len(msg).to_bytes(4, byteorder='big') + msg

        s.sendall(msg)

        print('Make Account Result:', s.recv(1024).hex())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testLogin(username, password):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if useSsl:
            s = context.wrap_socket(s, server_hostname='73.11.102.15')
        s.connect((address, port))
        
        msg = b'b' + username + b'@' + password
        msg = len(msg).to_bytes(4, byteorder='big') + msg
        
        s.sendall(msg)

        global token
        token = s.recv(1024)

        print('Login Result:', token.hex())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testRunAnalysis(username, path, t=token):
    f = open(path, 'rb')
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if useSsl:
            s = context.wrap_socket(s, server_hostname='73.11.102.15')
        s.connect((address, port))

        msg = b'c' + t + b'|'
        
        buf = f.read(4096)
        while buf:
            msg += buf
            buf = f.read(4096)

        msg = len(msg).to_bytes(4, byteorder='big') + msg

        s.sendall(msg)

        print('Run Analysis Results:', s.recv(1024).decode())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testGetReportList(username, t=token):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if useSsl:
            s = context.wrap_socket(s, server_hostname='73.11.102.15')
        s.connect((address, port))
        
        msg = b'd' + t
        msg = len(msg).to_bytes(4, byteorder='big') + msg
        
        s.sendall(msg)

        print('Get Report List Results:', s.recv(1024).decode())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testGetReport(username, reportID, t=token):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if useSsl:
            s = context.wrap_socket(s, server_hostname='73.11.102.15')
        s.connect((address, port))
        
        msg = b'e' + t + b'|' + reportID.to_bytes(4, 'big')
        msg = len(msg).to_bytes(4, byteorder='big') + msg

        s.sendall(msg)

        print('Get Report Results:', s.recv(1024).decode())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testLogout(username, t=token):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if useSsl:
            s = context.wrap_socket(s, server_hostname='73.11.102.15')
        s.connect((address, port))
        
        msg = b'z' + t
        msg = len(msg).to_bytes(4, byteorder='big') + msg
        
        s.sendall(msg)

        print('Logged Out')
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()



if __name__ == "__main__":
    testMakeAccount(b'UserName', b'Password')
    testLogin(b'UserName', b'Password')
    testRunAnalysis(b'UserName', b'IMG_1332.JPG', token) # Only works on my local machine (obviously)
    testGetReportList(b'UserName', token)
    testGetReport(b'UserName', 1, token)
    testLogout(b'UserName', token)
    testGetReportList(b'UserName', token)




