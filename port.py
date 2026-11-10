import socket

for p in range(4470, 65536):
    s = socket.socket()
    try:
        s.bind(("0.0.0.0", p))
        print(p)
        break
    except OSError:
        s.close()
