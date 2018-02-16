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



def testMakeAccount():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        
        msg = b'aUserName@Password'

        s.sendall(msg)

        s.shutdown(socket.SHUT_WR)

        print('Make Account Result:', s.recv(1024).hex())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testLogin():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))
        
        msg = b'bUserName@Password'

        s.sendall(msg)

        s.shutdown(socket.SHUT_WR)

        print('Login Result:', s.recv(1024).hex())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()

def testRunAnalysis(path):
    f = open(path, 'rb')
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', port))

        msg = b'cUserName@Password|'

        s.sendall(msg)
        
        buf = f.read(4096)
        while buf:
            s.sendall(buf)
            buf = f.read(4096)

        s.shutdown(socket.SHUT_WR)

        print(s.recv(1024).decode())
    except (ConnectionRefusedError, socket.gaierror):
        print ('Connection failed')
    finally:
        s.close()


        
testMakeAccount()
testLogin()
testRunAnalysis('/Users/quanah/Desktop/test.jpg') # Only works on my local machine (obviously)


