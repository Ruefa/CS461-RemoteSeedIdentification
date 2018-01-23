import socket
import sys

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 5777

f = open(sys.argv[1], 'rb')

try:
    s.connect(('localhost', port))
    
    buf = f.read(4096)
    while buf:
        s.sendall(buf)
        buf = f.read(4096)

    print("File Sent")

    s.shutdown(socket.SHUT_WR)

    print(s.recv(1024).decode())
except (ConnectionRefusedError, socket.gaierror):
    print ('Connection failed')
finally:
    s.close()

        

