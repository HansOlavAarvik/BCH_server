import socket


def receive_udp_data(ip_address="0.0.0.0", port=3390):
    """
    Receive UDP data from a specific IP address on the given port.
    
    Parameters:
    
    """
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Bind the socket to the port
    server_address = (ip_address, port)
    print(f"Starting UDP server on {ip_address}:{port}")
    sock.bind(server_address)
    
    try:
        while True:
            # Receive data
            print("\nWaiting to receive message...")
            data, address = sock.recvfrom(4096)
            
            print(f"Received {len(data)} bytes from {address}")
            print(f"Data: {data.decode('utf-8', errors='replace')}")
            
            # Optionally, you can also print data as bytes or hex
            print(f"Raw data: {data}")
            print(f"Hex data: {data.hex()}")
            
    except KeyboardInterrupt:
        print("Server stopped by user")
    finally:
        sock.close()
        print("Socket closed")

if __name__ == "__main__":

    stm32_ip = "192.168.1.111"  # Replace with your STM32's static IP
    listen_port = 3390  # Port to listen on
    
    # To listen only for the specific STM32 device, use its IP:
    # receive_udp_data(stm32_ip, listen_port)
    
    # To listen for any device (recommended for testing):
    receive_udp_data("0.0.0.0", listen_port)