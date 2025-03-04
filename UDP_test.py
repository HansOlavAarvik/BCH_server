import socket

UDP_IP = "192.168.1.111"
UDP_PORT = 6000  # Replace with your UDP port
MESSAGE = b"Hello from computer"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))