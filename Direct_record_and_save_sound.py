import socket
import threading
import time
import os
import struct
import wave
import collections

# Configuration
UDP_LISTEN_IP = "0.0.0.0"    # Listen on all interfaces
UDP_LISTEN_PORT = 6000       # Port to listen on for audio (same as STM32 sends to)
SAMPLE_RATE = 32000          # 32 kHz (match your I2S configuration)
HEADER_SIZE = 8              # Size of our UDP packet header

# Audio file settings
AUDIO_FILE = "recorded_audio.wav"
CHANNELS = 1                 # Mono
SAMPLE_WIDTH = 2             # 16-bit audio (2 bytes) - you're sending 16-bit samples!

# Buffer to reassemble chunked packets
packet_buffer = {}
last_sequence = -1

# Create socket
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listen_sock.bind((UDP_LISTEN_IP, UDP_LISTEN_PORT))

# Flag to control the listening thread
running = True

# Create a WAV file for writing audio data
wf = wave.open(AUDIO_FILE, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(SAMPLE_WIDTH)
wf.setframerate(SAMPLE_RATE)

# Stats
stats = {
    'packets_received': 0,
    'packets_written': 0,
    'bytes_written': 0,
    'start_time': time.time()
}

def listen_for_audio():
    print(f"UDP server listening for audio on port {UDP_LISTEN_PORT}")
    global last_sequence
    
    while running:
        try:
            data, addr = listen_sock.recvfrom(4096)
            stats['packets_received'] += 1
            
            if len(data) < HEADER_SIZE:
                print(f"Warning: Packet too small ({len(data)} bytes)")
                continue
                
            # Parse header
            sequence = (data[0] << 8) | data[1]
            chunk_index = data[2]
            chunk_count = data[3]
            timestamp = (data[4] << 24) | (data[5] << 16) | (data[6] << 8) | data[7]
            
            # Audio data starts after header
            audio_chunk = data[HEADER_SIZE:]
            
            # Handle single chunk packets (most common case)
            if chunk_count == 1:
                wf.writeframes(audio_chunk)
                stats['bytes_written'] += len(audio_chunk)
                stats['packets_written'] += 1
                last_sequence = sequence
            else:
                # Multi-chunk packet reassembly
                if sequence not in packet_buffer:
                    packet_buffer[sequence] = [None] * chunk_count
                
                # Store this chunk
                packet_buffer[sequence][chunk_index] = audio_chunk
                
                # Check if we have all chunks for this sequence
                if all(chunk is not None for chunk in packet_buffer[sequence]):
                    # Reassemble complete packet
                    complete_audio = b''.join(packet_buffer[sequence])
                    wf.writeframes(complete_audio)
                    stats['bytes_written'] += len(complete_audio)
                    stats['packets_written'] += 1
                    del packet_buffer[sequence]
                    
                    if sequence > last_sequence or last_sequence - sequence > 32768:
                        last_sequence = sequence
            
            # Print stats occasionally
            if stats['packets_received'] % 100 == 0:
                elapsed = time.time() - stats['start_time']
                duration = stats['bytes_written'] / (SAMPLE_RATE * SAMPLE_WIDTH * CHANNELS)
                print(f"Stats: Received {stats['packets_received']} packets, "
                      f"Written {stats['packets_written']} packets, "
                      f"Audio: {duration:.1f} seconds, "
                      f"Rate: {stats['packets_received']/elapsed:.1f} packets/sec")
            
            # Clean up old pending packets
            old_seq_threshold = (last_sequence - 30) % 65536
            for seq in list(packet_buffer.keys()):
                if (seq < old_seq_threshold and old_seq_threshold > 30) or \
                   (seq > old_seq_threshold + 30000):  # Handle wraparound
                    del packet_buffer[seq]
            
        except Exception as e:
            if running:  # Only show error if we're still supposed to be running
                print(f"Error receiving: {e}")
            else:
                break

# Start the listening thread
listen_thread = threading.Thread(target=listen_for_audio)
listen_thread.daemon = True
listen_thread.start()

# Main control loop
try:
    print(f"Recording audio to {AUDIO_FILE}")
    print("Press Ctrl+C to stop recording and save the file")
    
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nStopping recording...")
finally:
    running = False
    listen_sock.close()
    wf.close()
    
    elapsed = time.time() - stats['start_time']
    duration = stats['bytes_written'] / (SAMPLE_RATE * SAMPLE_WIDTH * CHANNELS)
    print(f"\nRecording finished:")
    print(f"- Duration: {duration:.2f} seconds")
    print(f"- Packets received: {stats['packets_received']}")
    print(f"- Packets written: {stats['packets_written']}")
    print(f"- Audio saved to: {AUDIO_FILE}")