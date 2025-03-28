import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', 6002))
print("Listening on UDP port 6002...")

while True:
    data, addr = s.recvfrom(4096)
    print(f"Received from {addr}: {data}")