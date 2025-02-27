import socket
import threading
import time

# Configuration
UDP_LISTEN_IP = "0.0.0.0"    # Listen on all interfaces
UDP_LISTEN_PORT = 6000       # Port to listen on
STM32_IP = "192.168.1.111"   # Replace with your STM32's IP address
STM32_PORT = 6000            # Port the STM32 is listening on

# Create sockets
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listen_sock.bind((UDP_LISTEN_IP, UDP_LISTEN_PORT))
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Flag to control the listening thread
running = True

def listen_for_messages():
    print(f"UDP server listening on port {UDP_LISTEN_PORT}")
    
    while running:
        try:
            data, addr = listen_sock.recvfrom(1024)
            message = data.decode()
            print(f"Received from {addr}: {message}")
            
            # Optional: Echo back the data
            # listen_sock.sendto(data, addr)
        except Exception as e:
            if running:  # Only show error if we're still supposed to be running
                print(f"Error receiving: {e}")
            break

# Start the listening thread
listen_thread = threading.Thread(target=listen_for_messages)
listen_thread.daemon = True
listen_thread.start()

# Main loop for sending messages
try:
    print(f"Ready to send messages to {STM32_IP}:{STM32_PORT}")
    print("Type a message and press Enter to send (or 'quit' to exit)")
    
    while True:
        message = input("> ")
        
        if message.lower() == 'quit':
            break

        send_sock.sendto(message.encode(), (STM32_IP, STM32_PORT))
        print(f"Sent: {message}")
        
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    # Clean up
    running = False
    send_sock.close()
    listen_sock.close()
    time.sleep(0.5)  # Give threads time to clean up