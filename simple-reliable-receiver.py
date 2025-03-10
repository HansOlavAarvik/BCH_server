import socket
import struct
import numpy as np
import pyaudio
import argparse
import time
import threading
import queue

def receive_and_play(listen_port=6001, stm32_ip="192.168.1.111", 
                     sample_rate=32000, buffer_size=4048,
                     jitter_buffer_ms=300):
    """
    Simplified but reliable UDP audio player with anti-crackling measures
    """
    print(f"\n=== AUDIO PLAYER ===")
    print(f"Target device: {stm32_ip}")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Buffer size: {buffer_size} samples")
    print(f"Jitter buffer: {jitter_buffer_ms} ms")
    print("=====================\n")
    
    # Socket setup with enlarged buffer
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
    udp_sock.bind(("0.0.0.0", listen_port))
    udp_sock.settimeout(0.1)
    
    # Calculate jitter buffer in packets
    jitter_packets = int((jitter_buffer_ms / 1000) * sample_rate / buffer_size) + 5
    
    # Audio queue with ample capacity
    audio_queue = queue.Queue(maxsize=jitter_packets * 3)
    
    # Control flags
    running = True
    buffer_ready = False
    
    # Initialize statistics
    packets_received = 0
    start_time = time.time()
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = None  # Will be created later
    
    def receive_thread_func():
        nonlocal packets_received, buffer_ready
        
        print(f"Waiting for audio from {stm32_ip}...")
        
        try:
            while running:
                try:
                    # Receive UDP packet
                    data, addr = udp_sock.recvfrom(8192)
                    
                    # Only accept packets from STM32
                    if addr[0] != stm32_ip:
                        continue
                    
                    # First packet info
                    if packets_received == 0:
                        print(f"First packet received: {len(data)} bytes")
                        samples = np.frombuffer(data, dtype=np.int16)
                        print(f"First few samples: {samples[:5]}")
                    
                    # Add to queue
                    try:
                        audio_queue.put(data, block=False)
                    except queue.Full:
                        # If queue is full, remove oldest packet
                        try:
                            audio_queue.get_nowait()
                            audio_queue.put_nowait(data)
                        except:
                            pass
                    
                    packets_received += 1
                    
                    # Fill initial buffer before starting playback
                    if not buffer_ready and audio_queue.qsize() >= jitter_packets // 2:
                        print(f"Buffer ready with {audio_queue.qsize()} packets. Starting playback...")
                        buffer_ready = True
                    
                    # Print stats periodically
                    if packets_received % 500 == 0:
                        elapsed = time.time() - start_time
                        rate = packets_received / elapsed if elapsed > 0 else 0
                        print(f"Received {packets_received} packets in {elapsed:.1f}s ({rate:.1f}/s)")
                        print(f"Buffer status: {audio_queue.qsize()}/{audio_queue.maxsize}")
                
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                    
            print("Receiver thread stopping...")
                
        except Exception as e:
            print(f"Receiver error: {e}")
    
    def playback_thread_func():
        nonlocal stream
        
        # Wait for buffer to fill initially
        print("Waiting for buffer to fill...")
        while running and not buffer_ready:
            time.sleep(0.1)
        
        if not running:
            return
            
        # Create audio stream once buffer is ready
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=sample_rate,
                        output=True,
                        frames_per_buffer=buffer_size)
        
        print("Starting audio playback")
        silence_counter = 0
        
        try:
            while running:
                try:
                    # Get data from queue with short timeout
                    audio_data = audio_queue.get(timeout=0.1)
                    silence_counter = 0
                    
                    # Write to audio stream
                    stream.write(audio_data)
                    
                except queue.Empty:
                    # Queue is empty, insert small amount of silence
                    silence_counter += 1
                    if silence_counter < 5:
                        silence = np.zeros(buffer_size, dtype=np.int16).tobytes()
                        stream.write(silence)
                    else:
                        # After several silence blocks, wait for more data
                        time.sleep(0.01)
        
        except Exception as e:
            print(f"Playback error: {e}")
        finally:
            print("Playback thread stopping...")
    
    # Start threads
    receiver_thread = threading.Thread(target=receive_thread_func)
    playback_thread = threading.Thread(target=playback_thread_func)
    
    receiver_thread.daemon = True
    playback_thread.daemon = True
    
    receiver_thread.start()
    playback_thread.start()
    
    # Main thread waits for keyboard interrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping audio playback...")
    finally:
        # Clean up
        running = False
        time.sleep(0.5)
        
        if stream:
            stream.stop_stream()
            stream.close()
        
        p.terminate()
        udp_sock.close()
        print("Audio player stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple Reliable Audio Player')
    parser.add_argument('--port', type=int, default=6001, help='UDP listen port')
    parser.add_argument('--stm32', type=str, default='192.168.1.111', help='STM32 IP address')
    parser.add_argument('--rate', type=int, default=32000, help='Audio sample rate (Hz)')
    parser.add_argument('--buffer', type=int, default=1024, help='Audio buffer size (samples)')
    parser.add_argument('--jitter', type=int, default=300, help='Jitter buffer size (ms)')
    args = parser.parse_args()
    
    receive_and_play(
        listen_port=args.port,
        stm32_ip=args.stm32,
        sample_rate=args.rate,
        buffer_size=args.buffer,
        jitter_buffer_ms=args.jitter
    )
