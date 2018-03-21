import socket, ssl
import threading

from connectionHandler import handleConn


useSsl = False

def serverInit(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    return s

def serverLoop():
    s = serverInit('', 5777)

    while True:
        conn, addr = s.accept()
        t = threading.Thread(target = handleConn, args=(conn,), daemon=False)
        t.start()
        # handleConn(conn)

def sslServerLoop():
    s = serverInit('', 5777)

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain('cert.pem')

    while True:
        conn, addr = s.accept()
        sslConn = context.wrap_socket(conn, server_side=True)
        t = threading.Thread(target = handleConn, args=(sslConn,), daemon=False)
        t.start()
        # handleConn(sslConn)

        
def start():
    if useSsl:
        sslServerLoop()
    else:
        serverLoop()

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
