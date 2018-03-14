import socket, ssl
from connectionHandler import handleConn

useSsl = True

def serverInit(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    return s

def serverLoop():
    s = serverInit('', 5777)

    while True:
        conn, addr = s.accept()
        handleConn(conn)

def sslServerLoop():
    s = serverInit('', 5777)

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('cert.pem')

    while True:
        conn, addr = s.accept()
        sslConn = context.wrap_socket(conn, server_side=True)
        handleConn(sslConn)

        
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

if useSsl:
    sslServerLoop()
else:
    serverLoop()
