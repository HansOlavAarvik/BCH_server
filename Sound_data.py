import socket
import threading
import wave
import numpy as np
import matplotlib.pyplot as plt
import pyaudio
import argparse
import os
import time
import select

class MicrophoneTool:
    def __init__(self, 
                 sample_rate=32000,
                 sample_width=2,       # 2 bytes (16-bit), 4 bytes (32-bit)
                 channels=1,
                 udp_port=6001,
                 output_file="recorded_audio.wav",
                 data_file="audio_data.txt"):
        
        # Audio configuration
        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.channels = channels
        
        # Network configuration
        self.udp_ip = "0.0.0.0"  # Listen on all interfaces
        self.udp_port = udp_port
        
        # File paths
        self.output_file = output_file
        self.data_file = data_file
        
        # Socket for receiving data
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.udp_ip, self.udp_port))
        
        # Audio playback
        self.audio = pyaudio.PyAudio()
        
        # Control flags
        self.running = False
        self.received_data = bytearray()
        
        # WAV file setup
        self.wf = None
        
    def start_recording(self):
        """Start listening for audio data over UDP"""
        self.running = True
        self.received_data = bytearray()
        
        # Set up WAV file
        self.wf = wave.open(self.output_file, 'wb')
        self.wf.setnchannels(self.channels)
        self.wf.setsampwidth(self.sample_width)
        self.wf.setframerate(self.sample_rate)
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        print(f"Started recording on port {self.udp_port}")
        print(f"Sample rate: {self.sample_rate} Hz")
        print(f"Sample width: {self.sample_width * 8} bits")
        print(f"Channels: {self.channels}")
        
    def stop_recording(self):
        """Stop recording and save the files"""
        if not self.running:
            return
            
        self.running = False
        
        try:
            self.sock.settimeout(1)  # Set timeout to exit recvfrom
        except Exception as e:
            print(f"Warning: Could not set socket timeout: {e}")
        
        # Wait for listen thread to finish
        if hasattr(self, 'listen_thread') and self.listen_thread.is_alive():
            self.listen_thread.join(2)
            
        # Close WAV file
        if self.wf:
            self.wf.close()
            
        # Save raw data to text file if we have data
        if len(self.received_data) > 0:
            self._save_data_to_file()
            print(f"Recording stopped. Audio saved to {self.output_file}")
            print(f"Raw data saved to {self.data_file}")
        else:
            print("Recording stopped. No data was received.")
        
    def _listen(self):
        """Thread function to listen for incoming audio data"""
        try:
            self.sock.settimeout(None)  # No timeout - blocking mode
            packet_count = 0
            last_update_time = time.time()
            
            # Print initial status message
            print("Recording... Press '2' in the menu to stop")
            print("Waiting for data...")
            
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(2048)
                    
                    # Add data to our buffer
                    self.received_data.extend(data)
                    
                    # Write to WAV file
                    self.wf.writeframes(data)
                    
                    # Only update status periodically to avoid flooding the console
                    packet_count += 1
                    current_time = time.time()
                    if current_time - last_update_time >= 2.0:  # Update every 2 seconds
                        total_kb = len(self.received_data) / 1024
                        duration = len(self.received_data) / (self.sample_rate * self.sample_width * self.channels)
                        print(f"\rPackets: {packet_count} | Data: {total_kb:.1f} KB | Duration: {duration:.1f}s", end="", flush=True)
                        last_update_time = current_time
                        
                except socket.timeout:
                    pass
                except Exception as e:
                    if self.running:  # Only show error if we're still supposed to be running
                        print(f"\nError receiving data: {e}")
                    break
        except Exception as e:
            print(f"\nError in listen thread: {e}")
        finally:
            print("")  # Print newline after the progress indicator
            # Ensure we set running to False when the thread exits
            self.running = False
    
    def _save_data_to_file(self):
        """Save the raw audio data as unsigned integers to a text file"""
        data_np = None
        
        # Convert based on sample width
        if self.sample_width == 2:  # 16-bit
            data_np = np.frombuffer(self.received_data, dtype=np.int16)
            # Convert to unsigned safely by using uint16
            data_np_unsigned = np.array(data_np, dtype=np.uint16)
            # Add offset to make all values positive (32768 = 2^15)
            # We need to handle this carefully to avoid overflow
            data_np_unsigned = np.where(data_np < 0, 
                                       data_np_unsigned + 32768, 
                                       data_np + 32768)
        elif self.sample_width == 4:  # 32-bit
            data_np = np.frombuffer(self.received_data, dtype=np.int32)
            # Convert to unsigned safely by using uint32
            data_np_unsigned = np.array(data_np, dtype=np.uint32)
            # Add offset to make all values positive (2^31)
            data_np_unsigned = np.where(data_np < 0, 
                                       data_np_unsigned + 2147483648, 
                                       data_np + 2147483648)
        else:
            print(f"Unsupported sample width: {self.sample_width}")
            return
            
        # Save as text file
        with open(self.data_file, 'w') as f:
            # Write header
            f.write(f"# Audio data: {len(data_np_unsigned)} samples\n")
            f.write(f"# Sample rate: {self.sample_rate} Hz\n")
            f.write(f"# Sample width: {self.sample_width * 8} bits\n")
            f.write("# Format: sample_number, value\n")
            
            # Write data
            for i, val in enumerate(data_np_unsigned):
                f.write(f"{i}, {val}\n")
                    
    def play_audio(self):
        """Play the recorded audio"""
        if not os.path.exists(self.output_file):
            print(f"Error: {self.output_file} not found")
            return
            
        # Open the WAV file
        wf = wave.open(self.output_file, 'rb')
        
        # Create audio stream
        stream = self.audio.open(
            format=self.audio.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True
        )
        
        # Read and play audio in chunks
        chunk_size = 1024
        data = wf.readframes(chunk_size)
        
        print("Playing audio...")
        
        while data:
            stream.write(data)
            data = wf.readframes(chunk_size)
            
        # Clean up
        stream.stop_stream()
        stream.close()
        wf.close()
        
        print("Playback complete")
        
    def plot_data(self):
        """Plot the audio data as a time graph"""
        if not os.path.exists(self.output_file):
            print(f"Error: {self.output_file} not found")
            return
            
        # Open the WAV file and read data
        wf = wave.open(self.output_file, 'rb')
        n_frames = wf.getnframes()
        data = wf.readframes(n_frames)
        
        # Convert to numpy array
        if wf.getsampwidth() == 2:
            data_np = np.frombuffer(data, dtype=np.int16)
        elif wf.getsampwidth() == 4:
            data_np = np.frombuffer(data, dtype=np.int32)
        else:
            print(f"Unsupported sample width: {wf.getsampwidth()}")
            return
            
        # Create time axis
        time = np.linspace(0, n_frames / wf.getframerate(), n_frames)
        
        # Plot
        plt.figure(figsize=(12, 6))
        plt.plot(time[:min(len(time), len(data_np))], data_np[:min(len(time), len(data_np))])
        plt.title('Audio Waveform')
        plt.xlabel('Time (seconds)')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.show()
        
        wf.close()
        
    def close(self):
        """Close all resources"""
        self.running = False
        
        # Close WAV file
        if hasattr(self, 'wf') and self.wf:
            try:
                self.wf.close()
            except Exception as e:
                print(f"Warning: Could not close WAV file: {e}")
        
        # Close audio
        try:
            self.audio.terminate()
        except Exception as e:
            print(f"Warning: Could not terminate audio: {e}")
        
        # Close socket
        try:
            self.sock.close()
        except Exception as e:
            print(f"Warning: Could not close socket: {e}")
        

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Microphone Testing Tool')
    parser.add_argument('--rate', type=int, default=32000, help='Sample rate in Hz')
    parser.add_argument('--width', type=int, default=2, choices=[2, 4], 
                        help='Sample width in bytes (2 for 16-bit, 4 for 32-bit)')
    parser.add_argument('--channels', type=int, default=1, help='Number of audio channels')
    parser.add_argument('--port', type=int, default=6001, help='UDP port to listen on')
    parser.add_argument('--output', default='recorded_audio.wav', help='Output WAV file')
    
    args = parser.parse_args()
    
    # Create tool instance
    tool = MicrophoneTool(
        sample_rate=args.rate,
        sample_width=args.width,
        channels=args.channels,
        udp_port=args.port,
        output_file=args.output
    )
    
    # Use a global flag to track recording state
    is_recording = False
    command_thread = None
    command_running = True
    
    def command_listener():
        """Thread that listens for keypresses during recording"""
        nonlocal is_recording, command_running
        
        print("Press 's' to stop recording, 'q' to quit")
        
        while command_running:
            try:
                choice = input().strip().lower()
                
                if choice == 's' and is_recording:
                    print("\nStopping recording...")
                    tool.stop_recording()
                    is_recording = False
                    break
                elif choice == 'q':
                    command_running = False
                    if is_recording:
                        tool.stop_recording()
                        is_recording = False
                    break
            except Exception:
                time.sleep(0.1)  # Avoid high CPU usage
    
    # Main menu loop
    try:
        while command_running:
            print("\nMicrophone Testing Tool")
            print("---------------------")
            print("1: Start recording")
            print("2: Stop recording")
            print("3: Play recorded audio")
            print("4: Plot audio data")
            print("5: Change settings")
            print("q: Quit")
            
            choice = input("\nEnter choice: ").strip().lower()
            
            if choice == '1':
                if not is_recording:
                    tool.start_recording()
                    is_recording = True
                    
                    # Create a thread to listen for commands during recording
                    command_thread = threading.Thread(target=command_listener)
                    command_thread.daemon = True
                    command_thread.start()
                    
                    # Wait for the command thread to complete
                    command_thread.join()
                else:
                    print("Already recording.")
                    
            elif choice == '2':
                if is_recording:
                    print("Stopping recording...")
                    tool.stop_recording()
                    is_recording = False
                else:
                    print("Not currently recording.")
                    
            elif choice == '3':
                tool.play_audio()
                
            elif choice == '4':
                tool.plot_data()
                
            elif choice == '5':
                print("\nCurrent Settings:")
                print(f"Sample rate: {tool.sample_rate} Hz")
                print(f"Sample width: {tool.sample_width * 8} bits")
                print(f"Channels: {tool.channels}")
                print(f"UDP port: {tool.udp_port}")
                
                print("\nChange settings:")
                rate = input("Sample rate (Hz) [leave empty to keep current]: ")
                if rate:
                    tool.sample_rate = int(rate)
                    
                width = input("Sample width (2 for 16-bit, 4 for 32-bit) [leave empty to keep current]: ")
                if width:
                    tool.sample_width = int(width)
                    
                channels = input("Channels [leave empty to keep current]: ")
                if channels:
                    tool.channels = int(channels)
                    
                port = input("UDP port [leave empty to keep current]: ")
                if port:
                    # Need to create a new socket with the new port
                    tool.sock.close()
                    tool.udp_port = int(port)
                    tool.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    tool.sock.bind((tool.udp_ip, tool.udp_port))
                    
                print("\nSettings updated")
                
            elif choice == 'q':
                break
                
            else:
                print("Invalid choice")
                
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        command_running = False
        tool.close()
        print("Goodbye!")

if __name__ == "__main__":
    main()