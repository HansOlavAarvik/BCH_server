import socket
import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def capture_and_visualize(listen_ip="0.0.0.0", listen_port=6001, 
                          stm32_ip="192.168.1.111", stm32_port=6000,
                          buffer_size=500):
    """Capture sound data via UDP and visualize it in real-time."""
    # Create UDP socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((listen_ip, listen_port))
    udp_sock.settimeout(0.1)  # Short timeout for responsive updates
    
    # Initialize data buffer
    data_buffer = np.zeros(buffer_size)
    
    # Set up the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    line, = ax.plot(range(buffer_size), data_buffer)
    
    # Set axis limits
    ax.set_xlim(0, buffer_size - 1)
    ax.set_ylim(-35000, 35000)  # Based on observed data range
    
    # Set labels and title
    ax.set_xlabel('Sample')
    ax.set_ylabel('Amplitude')
    ax.set_title('Real-time Audio Waveform')
    ax.grid(True)
    
    # Processing buffer
    raw_buffer = bytearray()
    
    # Send start signal
    udp_sock.sendto(b"START", (stm32_ip, stm32_port))
    
    def update(frame):
        nonlocal raw_buffer, data_buffer
        
        try:
            # Try to receive data
            data, addr = udp_sock.recvfrom(4096)
            raw_buffer.extend(data)
            
            # Extract samples (assuming 16-bit little-endian)
            while len(raw_buffer) >= 8:  # Each sample group is 8 bytes: [sample, 2, 0, 0]
                # Get just the audio sample (first value)
                value = struct.unpack('<h', raw_buffer[:2])[0]
                # Skip the whole group (sample, 2, 0, 0)
                raw_buffer = raw_buffer[8:]
                
                # Shift the buffer left and add new sample
                data_buffer = np.roll(data_buffer, -1)
                data_buffer[-1] = value
        
        except socket.timeout:
            # No data received, just continue
            pass
        
        # Update the line data
        line.set_ydata(data_buffer)
        return line,
    
    # Set up animation
    ani = FuncAnimation(fig, update, interval=30, blit=True)
    
    try:
        plt.tight_layout()
        plt.show()
    except KeyboardInterrupt:
        print("Visualization stopped by user")
    finally:
        # Send stop signal
        udp_sock.sendto(b"STOP", (stm32_ip, stm32_port))
        udp_sock.close()
        print("Socket closed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Visualize sound data')
    parser.add_argument('--stm32-ip', default='192.168.1.111', help='STM32 IP address')
    parser.add_argument('--stm32-port', type=int, default=6000, help='STM32 port')
    parser.add_argument('--listen-port', type=int, default=6001, help='Local listen port')
    parser.add_argument('--buffer', type=int, default=500, help='Visualization buffer size')
    args = parser.parse_args()
    
    capture_and_visualize(stm32_ip=args.stm32_ip, stm32_port=args.stm32_port,
                         listen_port=args.listen_port, buffer_size=args.buffer)