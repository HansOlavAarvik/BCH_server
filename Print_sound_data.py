import socket
import struct
import argparse
import time

def capture_sound_udp(listen_ip="0.0.0.0", listen_port=6001, 
                      stm32_ip="192.168.1.111", stm32_port=6000,
                      samples_per_piece=10, sample_size=2, format_code='<h'):
    """Capture sound data from microcontroller via UDP and print as integers."""
    # Create UDP socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((listen_ip, listen_port))
    udp_sock.settimeout(1.0)  # 1 second timeout for receiving
    
    print(f"Listening for UDP sound data on {listen_ip}:{listen_port}")
    print(f"Will capture in pieces of {samples_per_piece} integers")
    print("Press Ctrl+C to stop")
    
    # Send a message to tell STM32 we're ready
    try:
        udp_sock.sendto(b"START", (stm32_ip, stm32_port))
        
        buffer = bytearray()
        piece_count = 0
        
        while True:
            try:
                # Receive UDP packet
                data, addr = udp_sock.recvfrom(4096)
                
                # Add to our processing buffer
                buffer.extend(data)
                
                # Process complete chunks
                # Each audio sample appears to be in a group of 4 values: [sample, 2, 0, 0]
                while len(buffer) >= samples_per_piece * 4 * sample_size:
                    piece = []
                    for _ in range(samples_per_piece):
                        if len(buffer) >= 4 * sample_size:
                            # Extract just the audio sample (first value in the group)
                            value = struct.unpack(format_code, buffer[:sample_size])[0]
                            piece.append(value)
                            # Skip the rest of the group (2, 0, 0)
                            buffer = buffer[4 * sample_size:]
                    
                    piece_count += 1
                    print(f"Piece #{piece_count}: {piece}")
                    
            except socket.timeout:
                # Just a timeout, continue waiting
                continue
                
    except KeyboardInterrupt:
        print("\nCapture stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Send stop signal and close socket
        try:
            udp_sock.sendto(b"STOP", (stm32_ip, stm32_port))
        except:
            pass
        udp_sock.close()
        print("UDP socket closed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Capture sound data via UDP')
    parser.add_argument('--stm32-ip', default='192.168.1.111', help='STM32 IP address')
    parser.add_argument('--stm32-port', type=int, default=6000, help='STM32 port')
    parser.add_argument('--listen-port', type=int, default=6001, help='Local listen port')
    parser.add_argument('--size', type=int, default=10, help='Samples per piece')
    args = parser.parse_args()
    
    capture_sound_udp(stm32_ip=args.stm32_ip, stm32_port=args.stm32_port,
                      listen_port=args.listen_port, samples_per_piece=args.size)