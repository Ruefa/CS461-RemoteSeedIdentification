import socket
import sys

# These are not extensive unit tests, just preliminary testing

# This code is awful and will be replaced with real tests eventually

port = 5777

# f = open(sys.argv[1], 'rb')


# try:
#     s.connect(('localhost', port))
#     
#     buf = f.read(4096)
#     while buf:
#         s.sendall(buf)
#         buf = f.read(4096)
# 
#     print("File Sent")
# 
#     s.shutdown(socket.SHUT_WR)
# 
#     print(s.recv(1024).decode())
# except (ConnectionRefusedError, socket.gaierror):
#     print ('Connection failed')
# finally:
#     s.close()


token = b''

def testMakeAccount(username, password):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        
        msg = b'a' + username + b'@' + password

        s.sendall(msg)

        s.shutdown(socket.SHUT_WR)

        print('Make Account Result:', s.recv(1024).hex())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testLogin(username, password):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        
        msg = b'b' + username + b'@' + password
        
        s.sendall(msg)

        s.shutdown(socket.SHUT_WR)

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
        s.connect(('localhost', port))

        msg = b'c' + t + b'|'
        
        s.sendall(msg)
        
        buf = f.read(4096)
        while buf:
            s.sendall(buf)
            buf = f.read(4096)

        s.shutdown(socket.SHUT_WR)

        print('Run Analysis Results:', s.recv(1024).decode())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testGetReportList(username, t=token):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        
        msg = b'd' + t
        
        s.sendall(msg)

        s.shutdown(socket.SHUT_WR)

        print('Get Report List Results:', s.recv(1024).decode())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testGetReport(username, reportID, t=token):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        
        msg = b'e' + t + b'|' + reportID.to_bytes(4, 'big')

        s.sendall(msg)

        s.shutdown(socket.SHUT_WR)

        print('Get Report Results:', s.recv(1024).decode())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testLogout(username, t=token):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        
        msg = b'z' + t
        
        s.sendall(msg)

        s.shutdown(socket.SHUT_WR)

        print('Logged Out')
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()



if __name__ == "__main__":
    testMakeAccount(b'UserName', b'Password')
    testLogin(b'UserName', b'Password')
    testRunAnalysis(b'UserName', b'/Users/quanah/Desktop/test.jpg', token) # Only works on my local machine (obviously)
    testGetReportList(b'UserName', token)
    testGetReport(b'UserName', 1, token)
    testLogout(b'UserName', token)
    testGetReportList(b'UserName', token)




