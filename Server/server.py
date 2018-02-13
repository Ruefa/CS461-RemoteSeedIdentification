import socket
from connectionHandler import handleConn

def serverInit():
    host = ''
    port = 5777 # arbitrary choice

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    return s

def serverLoop():
    s = serverInit()

    while True:
        conn, addr = s.accept()
        handleConn(conn)

        
#def handleConn(conn):
#    f = open('ReceivedImg.jpg', 'wb')
#
#    buf = conn.recv(4096)
#    while buf:
#        f.write(buf)
#        buf = conn.recv(4096)
#
#    print("File Received")
#
#    conn.send("Image Received\n".encode())
#
#    conn.close()


serverLoop()
