import socket
import threading
import time
import os
import struct
import wave

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
SAMPLE_WIDTH = 2             # 32-bit audio (4 bytes)
SAMPLE_RATE = 32000          # 32 kHz (match your I2S configuration)

# Create sockets
listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listen_sock.bind((UDP_LISTEN_IP, UDP_LISTEN_PORT))
send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Flag to control the listening thread
running = True

# Create a WAV file for writing audio data
wf = wave.open(AUDIO_FILE, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(SAMPLE_WIDTH)
wf.setframerate(SAMPLE_RATE)

def listen_for_audio():
    print(f"UDP server listening for audio on port {UDP_LISTEN_PORT}")
    
    while running:
        try:
            data, addr = listen_sock.recvfrom(2048)
            
            # Write the raw data to the WAV file
            # Note: We're assuming the STM32 sends properly formatted 32-bit PCM samples
            # If your data needs conversion, you'd do that here
            wf.writeframes(data)
            
            # Print status (optional - for debugging)
            print(f"Received {len(data)} bytes of audio data from {addr[0]}:{addr[1]}")
            
        except Exception as e:
            if running:  # Only show error if we're still supposed to be running
                print(f"Error receiving: {e}")
            break

# Start the listening thread
listen_thread = threading.Thread(target=listen_for_audio)
listen_thread.daemon = True
listen_thread.start()

# Main loop for sending messages
try:
    print(f"Ready to send messages to {STM32_IP}:{STM32_PORT}")
    print("Type a message and press Enter to send (or 'quit' to exit)")
    print("Audio data is being saved to", AUDIO_FILE)
    
    while True:
        message = input("> ")
        
        if message.lower() == 'quit':
            break

        send_sock.sendto(message.encode(), (STM32_IP, STM32_PORT))
        print(f"Sent: {message}")
        
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    running = False
    send_sock.close()
    listen_sock.close()
    wf.close()  # Close the WAV file
    print(f"Audio saved to {AUDIO_FILE}")
    time.sleep(0.5)  # Give threads time to clean up