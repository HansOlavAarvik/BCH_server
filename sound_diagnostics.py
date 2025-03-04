import socket
import threading
import time
import os
import struct
import wave
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Configuration
UDP_LISTEN_IP = "0.0.0.0"    # Listen on all interfaces
UDP_LISTEN_PORT = 6001       # Port to listen on for audio
TEMPHUMID_PORT = 6002        # Port for temperature/humidity data
BUTTON_PORT = 6003           # Port for button presses
STM32_IP = "192.168.1.111"   # Replace with your STM32's IP address
STM32_PORT = 6000            # Port the STM32 is listening on

# Audio file settings
AUDIO_FILE = "recorded_audio.wav"
CHANNELS = 1                 # Mono
SAMPLE_WIDTH = 3             # 24-bit audio (3 bytes) - matches STM32 I2S config
SAMPLE_RATE = 32000          # 32 kHz (match your I2S configuration)

# Create a debug/raw file to store the exact data received for analysis
RAW_DATA_FILE = "raw_audio_data.bin"
raw_file = open(RAW_DATA_FILE, "wb")

# Create sockets
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listen_sock.bind((UDP_LISTEN_IP, UDP_LISTEN_PORT))
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Flag to control the listening thread
running = True

# Create a WAV file for writing audio data
wf = wave.open(AUDIO_FILE, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(4)  # Using 4 bytes per sample for WAV file (32-bit)
wf.setframerate(SAMPLE_RATE)

# For diagnostics
packet_count = 0
total_bytes = 0
packet_sizes = []
data_samples = []  # Store some samples for analysis

def convert_24bit_to_32bit_wav(data_24bit):
    """
    Convert 24-bit data to 32-bit WAV compatible format.
    Handle sign extension properly.
    """
    # Determine how many 3-byte samples we have
    num_samples = len(data_24bit) // 3
    
    # Prepare a buffer for 32-bit output
    data_32bit = bytearray(num_samples * 4)
    
    for i in range(num_samples):
        # Extract 3 bytes (24-bit sample)
        byte0 = data_24bit[i*3]
        byte1 = data_24bit[i*3+1]
        byte2 = data_24bit[i*3+2]
        
        # Convert to a signed 32-bit integer with proper sign extension
        # Assuming the data is little-endian (LSB first)
        value = byte0 | (byte1 << 8) | (byte2 << 16)
        
        # Sign extend from 24-bit to 32-bit
        if value & 0x800000:  # Check if sign bit (bit 23) is set
            value |= 0xFF000000  # Set bits 24-31 to 1s
        
        # Pack as 32-bit little-endian integer
        struct.pack_into("<i", data_32bit, i*4, value)
    
    return bytes(data_32bit)

def analyze_packet(data, packet_num):
    """Analyze packet data and print diagnostic information"""
    global data_samples
    
    # Store some samples for later analysis (up to 1000 samples)
    if len(data_samples) < 1000:
        # Convert bytes to int values for analysis
        # Assuming 24-bit data in 3-byte chunks
        num_samples = len(data) // 3
        for i in range(min(num_samples, 100)):  # Get up to 100 samples per packet
            if len(data_samples) < 1000:
                # Extract 3 bytes (24-bit sample)
                byte0 = data[i*3] if i*3 < len(data) else 0
                byte1 = data[i*3+1] if i*3+1 < len(data) else 0
                byte2 = data[i*3+2] if i*3+2 < len(data) else 0
                
                # Convert to a signed integer
                value = byte0 | (byte1 << 8) | (byte2 << 16)
                
                # Sign extend if needed
                if value & 0x800000:
                    value |= 0xFF000000
                
                data_samples.append(value)
    
    # Basic statistics
    print(f"Packet {packet_num}: {len(data)} bytes")
    
    # Print first few bytes for inspection
    if len(data) >= 12:
        print(f"First 12 bytes: {data[:12].hex(' ')}")
    else:
        print(f"Data hex: {data.hex(' ')}")
    
    # Check if data length is divisible by expected sample size
    if len(data) % 3 != 0:
        print(f"WARNING: Data length ({len(data)}) is not divisible by 3 (24-bit samples)")

def listen_for_audio():
    print(f"UDP server listening for audio on port {UDP_LISTEN_PORT}")
    global packet_count, total_bytes, packet_sizes
    
    while running:
        try:
            data, addr = listen_sock.recvfrom(2048)
            
            # Write raw data to file for later analysis
            raw_file.write(data)
            raw_file.flush()
            
            # Update statistics
            packet_count += 1
            total_bytes += len(data)
            packet_sizes.append(len(data))
            
            # Analyze packet content (only do detailed analysis for first few packets)
            if packet_count <= 10 or packet_count % 100 == 0:
                analyze_packet(data, packet_count)
            
            # Convert 24-bit data to 32-bit for WAV file
            converted_data = convert_24bit_to_32bit_wav(data)
            wf.writeframes(converted_data)
            
            # Print less verbose status updates
            if packet_count % 100 == 0:
                print(f"Received {packet_count} packets, total: {total_bytes/1024:.2f} KB")
            
        except Exception as e:
            if running:  # Only show error if we're still supposed to be running
                print(f"Error receiving: {e}")
            break

def plot_audio_data():
    """Create a diagnostic plot of the received audio data"""
    if not data_samples:
        print("No audio data to plot")
        return
    
    plt.figure(figsize=(10, 6))
    
    # Plot raw samples
    plt.subplot(2, 1, 1)
    plt.plot(data_samples)
    plt.title('Raw Audio Samples')
    plt.xlabel('Sample Index')
    plt.ylabel('Amplitude')
    plt.grid(True)
    
    # Plot histogram to see distribution
    plt.subplot(2, 1, 2)
    plt.hist(data_samples, bins=50)
    plt.title('Amplitude Distribution')
    plt.xlabel('Amplitude Value')
    plt.ylabel('Frequency')
    plt.grid(True)
    
    # Save the plot
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    plot_filename = f"audio_analysis_{timestamp}.png"
    plt.tight_layout()
    plt.savefig(plot_filename)
    print(f"Saved analysis plot to {plot_filename}")
    
    # Optional: display the plot
    # plt.show()

# Start the listening thread
listen_thread = threading.Thread(target=listen_for_audio)
listen_thread.daemon = True
listen_thread.start()

# Main loop for sending messages
try:
    print(f"Ready to send messages to {STM32_IP}:{STM32_PORT}")
    print("Type a message and press Enter to send (or 'quit' to exit)")
    print("Audio data is being saved to", AUDIO_FILE)
    print("Raw binary data is being saved to", RAW_DATA_FILE)
    
    while True:
        message = input("> ")
        
        if message.lower() == 'quit':
            break
        elif message.lower() == 'stats':
            # Print detailed statistics
            if packet_count > 0:
                print(f"\n--- Statistics after {packet_count} packets ---")
                print(f"Total data received: {total_bytes/1024:.2f} KB")
                print(f"Average packet size: {total_bytes/packet_count:.2f} bytes")
                if packet_sizes:
                    print(f"Min packet size: {min(packet_sizes)} bytes")
                    print(f"Max packet size: {max(packet_sizes)} bytes")
                print(f"Estimated duration: {total_bytes/(SAMPLE_WIDTH*SAMPLE_RATE*CHANNELS):.2f} seconds")
                
                # Generate plot if matplotlib is available
                try:
                    plot_audio_data()
                except Exception as e:
                    print(f"Could not generate plot: {e}")
            else:
                print("No packets received yet")
            continue

        send_sock.sendto(message.encode(), (STM32_IP, STM32_PORT))
        print(f"Sent: {message}")
        
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    running = False
    send_sock.close()
    listen_sock.close()
    wf.close()  # Close the WAV file
    raw_file.close()  # Close the raw data file
    print(f"Audio saved to {AUDIO_FILE}")
    print(f"Raw data saved to {RAW_DATA_FILE}")
    
    # Final statistics and plot
    if packet_count > 0:
        try:
            plot_audio_data()
        except Exception as e:
            print(f"Could not generate final plot: {e}")
    
    time.sleep(0.5)  # Give threads time to clean up