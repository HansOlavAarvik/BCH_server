import socket
import struct
import pyaudio
import argparse
import time
import threading
import queue

def receive_and_play(listen_ip="0.0.0.0", listen_port=6001, 
                     stm32_ip="192.168.1.111", sample_rate=int(32018/2), 
                     buffer_size=2048, jitter_buffer_ms=200):
    """
    Improved UDP audio receiver with continuous streaming focus
    """
    # Print settings info
    print(f"\n=== AUDIO STREAM SETTINGS ===")
    print(f"Listening on port: {listen_port}")
    print(f"Accepting packets from: {stm32_ip}")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Jitter buffer: {jitter_buffer_ms} ms")
    print("=============================\n")
    
    # Calculate jitter buffer size
    jitter_buffer_packets = max(10, int((jitter_buffer_ms / 1000) * (sample_rate / buffer_size) * 2))
    print(f"Using jitter buffer of {jitter_buffer_packets} packets")
    
    # Create UDP socket with larger receive buffer
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set socket receive buffer to a larger size
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)  # 256KB receive buffer
    udp_sock.bind((listen_ip, listen_port))
    udp_sock.settimeout(0.1)
    
    # Create a queue for audio data
    audio_queue = queue.Queue(maxsize=jitter_buffer_packets * 2)
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Open audio stream with larger buffer
    stream = p.open(format=pyaudio.paInt16,
                    channels=1, 
                    rate=sample_rate,
                    output=True,
                    frames_per_buffer=buffer_size)
    
    # Shared flags and counters
    running = True
    packet_count = 0
    last_report_time = time.time()
    has_started = False  # Flag to track first packet
    
    def receive_audio():
        """Thread function to receive UDP audio data and fill the queue."""
        nonlocal packet_count, last_report_time, has_started
        
        try:
            print(f"Waiting for audio stream from {stm32_ip}...")
            
            while running:
                try:
                    # Receive UDP packet
                    data, addr = udp_sock.recvfrom(4096)
                    
                    # Only accept packets from STM32 IP
                    if addr[0] != stm32_ip:
                        continue
                    
                    # Report first packet only once at the beginning
                    if not has_started:
                        has_started = True
                        print(f"Audio stream connected from {addr[0]}:{addr[1]}")
                        print(f"Packet size: {len(data)} bytes")
                        if len(data) >= 8:
                            samples = struct.unpack(f"<{len(data)//2}h", data)
                            print(f"Sample values: {samples[:4]}...")
                        print("Buffering audio data...")
                    
                    packet_count += 1
                    
                    # Report stats every 5 seconds
                    current_time = time.time()
                    if current_time - last_report_time >= 5:
                        packets_per_second = packet_count / (current_time - last_report_time)
                        print(f"Receiving {packets_per_second:.1f} packets/sec, buffer: {audio_queue.qsize()}/{audio_queue.maxsize}")
                        packet_count = 0
                        last_report_time = current_time
                    
                    # Add data to queue, with timeout
                    try:
                        audio_queue.put(data, block=True, timeout=0.5)
                    except queue.Full:
                        # If queue is full, drop oldest data for real-time
                        audio_queue.get_nowait()
                        audio_queue.put_nowait(data)
                
                except socket.timeout:
                    # Just a timeout, continue
                    continue
                    
        except Exception as e:
            print(f"Receiver error: {e}")
        finally:
            if running:
                print("Receive thread stopping...")
    
    def play_audio():
        """Thread function to play audio from the queue."""
        nonlocal has_started
        
        # Wait for initial buffering
        buffer_target = jitter_buffer_packets // 2
        
        try:
            print("Playback thread ready...")
            
            # Wait for first audio data
            while running and not has_started:
                time.sleep(0.1)
                
            # Once started, wait for buffer to fill
            if running:
                while audio_queue.qsize() < buffer_target and running:
                    time.sleep(0.05)
                print(f"Starting playback with {audio_queue.qsize()} buffered packets")
            
            # Counter for silence insertion
            silence_runs = 0
            
            # Continuous playback loop
            while running:
                try:
                    # Get audio data with a short timeout
                    audio_data = audio_queue.get(timeout=0.02)
                    silence_runs = 0
                    
                    # Play audio
                    stream.write(audio_data)
                    
                    # Mark task as done
                    audio_queue.task_done()
                    
                except queue.Empty:
                    # If queue empty, insert small silence to prevent clicks
                    silence_runs += 1
                    if silence_runs < 5:
                        # Short silence for small gaps
                        silence = b'\x00' * buffer_size * 2
                        stream.write(silence)
                    else:
                        # For longer gaps, just sleep
                        time.sleep(0.01)
                        
                        # If we've been without audio for too long, re-buffer
                        if silence_runs > 50:
                            print("\nStream interrupted, waiting for data...")
                            # Wait for some data to arrive
                            while audio_queue.qsize() < buffer_target and running:
                                time.sleep(0.05)
                                if not running:
                                    break
                            if running:
                                print(f"Resuming playback with {audio_queue.qsize()} buffered packets")
                                silence_runs = 0
                
        except Exception as e:
            print(f"Playback error: {e}")
        finally:
            if running:
                print("Playback thread stopping...")
    
    # Start threads
    receive_thread = threading.Thread(target=receive_audio)
    play_thread = threading.Thread(target=play_audio)
    
    receive_thread.daemon = True
    play_thread.daemon = True
    
    receive_thread.start()
    play_thread.start()
    
    # Main thread processes keyboard interrupts
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping audio playback...")
    finally:
        # Clean up
        running = False
        time.sleep(0.5)
        
        # Close everything
        stream.stop_stream()
        stream.close()
        p.terminate()
        udp_sock.close()
        print("Audio playback stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Continuous STM32 UDP Audio Player')
    
    parser.add_argument('--port', type=int, default=6001, 
                        help='UDP listen port')
    parser.add_argument('--stm32', type=str, default="192.168.1.111", 
                        help='STM32 IP address')
    parser.add_argument('--rate', type=int, default=int(32018/2), 
                        help='Audio sample rate (Hz)')
    parser.add_argument('--buffer', type=int, default=2048, 
                        help='Audio buffer size (samples)')
    parser.add_argument('--jitter', type=int, default=200, 
                        help='Jitter buffer (ms)')
    
    args = parser.parse_args()
    
    receive_and_play(
        listen_port=args.port,
        stm32_ip=args.stm32,
        sample_rate=args.rate,
        buffer_size=args.buffer,
        jitter_buffer_ms=args.jitter
    )