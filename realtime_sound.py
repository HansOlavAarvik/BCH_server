import socket
import struct
import numpy as np
import pyaudio
import argparse
import time
import threading
import queue

def receive_and_play(listen_ip="0.0.0.0", listen_port=6001, 
                     sample_rate=32000, buffer_size=1024):
    """
    Simple UDP audio receiver and player designed to work with
    the processed STM32 audio data.
    """
    # Create UDP socket
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((listen_ip, listen_port))
    udp_sock.settimeout(0.1)  # Short timeout for responsiveness
    
    # Create a queue for audio data
    audio_queue = queue.Queue(maxsize=20)  # Buffer for smooth playback
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Open audio stream
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    output=True,
                    frames_per_buffer=buffer_size)
    
    # Flag to control the threads
    running = True
    
    # Statistics
    total_packets = 0
    start_time = time.time()
    
    def receive_audio():
        """Thread function to receive UDP audio data and fill the queue."""
        nonlocal total_packets, start_time  # Add start_time here
        
        try:
            print(f"Listening for audio data on UDP port {listen_port}")
            print(f"Playing at {sample_rate} Hz sample rate")
            print("Press Ctrl+C to stop")
            
            while running:
                # Rest of your code remains the same
                    try:
                        # Receive UDP packet
                        data, addr = udp_sock.recvfrom(8192)
                        total_packets += 1
                        
                        # For statistics every 5 seconds
                        if total_packets % 100 == 0:
                            elapsed = time.time() - start_time
                            if elapsed >= 5:
                                print(f"Received {total_packets} packets in {elapsed:.1f} seconds")
                                total_packets = 0
                                start_time = time.time()
                        
                        # Add received data to the queue
                        try:
                            audio_queue.put(data, timeout=0.5)
                        except queue.Full:
                            # If queue is full, remove oldest data to prevent delay
                            try:
                                audio_queue.get_nowait()
                                audio_queue.put(data, timeout=0.1)
                            except:
                                pass
                    
                    except socket.timeout:
                        # Just a timeout, continue
                        continue
                        
        except Exception as e:
            print(f"Error in receive thread: {e}")
        finally:
            if running:
                print("Receive thread stopping...")
    
    def play_audio():
        """Thread function to play audio from the queue."""
        try:
            while running:
                try:
                    # Get audio data from queue with timeout
                    audio_data = audio_queue.get(timeout=0.5)
                    
                    # Play the audio
                    stream.write(audio_data)
                    
                    # Mark as done
                    audio_queue.task_done()
                    
                except queue.Empty:
                    # Queue is empty, wait a bit
                    time.sleep(0.1)
                    continue
                    
        except Exception as e:
            print(f"Error in playback thread: {e}")
        finally:
            if running:
                print("Playback thread stopping...")
    
    # Start the receiver and player threads
    receive_thread = threading.Thread(target=receive_audio)
    play_thread = threading.Thread(target=play_audio)
    
    receive_thread.daemon = True
    play_thread.daemon = True
    
    receive_thread.start()
    play_thread.start()
    
    # Main thread just waits for keyboard interrupt
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping audio playback...")
    finally:
        # Clean up
        running = False
        
        # Wait for threads to finish
        time.sleep(0.5)
        
        # Close the audio stream and socket
        stream.stop_stream()
        stream.close()
        p.terminate()
        udp_sock.close()
        
        print("Audio playback stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Simple UDP Audio Player')
    parser.add_argument('--port', type=int, default=6001, help='UDP listen port')
    parser.add_argument('--rate', type=int, default=32000, help='Audio sample rate')
    parser.add_argument('--buffer', type=int, default=1024, help='Audio buffer size')
    args = parser.parse_args()
    
    receive_and_play(listen_port=args.port, sample_rate=args.rate, buffer_size=args.buffer)