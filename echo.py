import socket

UDP_IP = "0.0.0.0"  # Listen on all interfaces
UDP_PORT = 6000     # Your chosen port

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
print(f"UDP server listening on port {UDP_PORT}")

while True:
    data, addr = sock.recvfrom(1024)
    print(f"Received from {addr}: {data.decode()}")
    sock.sendto(data, addr)  # Echo back the data