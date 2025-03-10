import socket
import struct
import numpy as np
import argparse
import time
import wave
import os
import pyaudio

def detect_sample_rate(listen_port=6001, stm32_ip="192.168.1.111"):
    """
    Tests multiple sample rates to find the correct one
    """
    # Create output directory
    if not os.path.exists("audio_diagnosis"):
        os.makedirs("audio_diagnosis")
    
    # Generate timestamp for filenames
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    print(f"\n=== SAMPLE RATE DETECTOR ===")
    print(f"Target device: {stm32_ip}")
    print(f"This tool will record audio at different sample rates")
    print(f"to determine the correct one.")
    print("==============================\n")
    
    # Socket setup
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("0.0.0.0", listen_port))
    udp_sock.settimeout(0.1)
    
    # Sample rates to test
    sample_rates = [16000, 32000, 44100, 48000]
    
    # First, determine the packet arrival rate
    print("Measuring packet arrival rate...")
    packet_count = 0
    start_time = time.time()
    packet_durations = []
    
    try:
        # Collect packet timing data for 5 seconds
        end_time = start_time + 5
        first_packet_time = None
        
        while time.time() < end_time:
            try:
                data, addr = udp_sock.recvfrom(8192)
                
                if addr[0] != stm32_ip:
                    continue
                
                # Record first packet time
                current_time = time.time()
                if first_packet_time is None:
                    first_packet_time = current_time
                    print(f"First packet received: {len(data)} bytes")
                
                # Calculate time since first packet
                packet_time = current_time - first_packet_time
                packet_durations.append((packet_count, packet_time))
                
                packet_count += 1
            except socket.timeout:
                continue
        
        # Calculate packet arrival rate
        if packet_count > 2:
            elapsed = time.time() - start_time
            packets_per_second = packet_count / elapsed
            print(f"Received {packet_count} packets in {elapsed:.1f} seconds")
            print(f"Packet rate: {packets_per_second:.1f} packets/second")
            
            # Calculate bytes per second
            total_bytes = sum(len(data) for data, _ in packet_durations)
            bytes_per_second = total_bytes / elapsed
            
            # Calculate samples per second (assuming 16-bit samples)
            samples_per_second = bytes_per_second / 2
            print(f"Estimated sample rate: {samples_per_second:.1f} Hz")
            
            # Guess ideal sample rate
            closest_rate = min(sample_rates, key=lambda x: abs(x - samples_per_second))
            print(f"Closest standard sample rate: {closest_rate} Hz")
            print(f"\nLet's test this rate and others...")
        else:
            print("Not enough packets received for analysis")
            return
    
    except Exception as e:
        print(f"Error in packet rate detection: {e}")
    
    # Now record short WAV files at different sample rates
    for rate in sample_rates:
        filename = f"audio_diagnosis/test_{rate}hz_{timestamp}.wav"
        print(f"\nRecording at {rate} Hz...")
        
        # Create WAV file
        wav_file = wave.open(filename, 'wb')
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(rate)
        
        # Record for 5 seconds
        start_time = time.time()
        end_time = start_time + 5
        packets_received = 0
        
        try:
            while time.time() < end_time:
                try:
                    data, addr = udp_sock.recvfrom(8192)
                    
                    if addr[0] != stm32_ip:
                        continue
                    
                    wav_file.writeframes(data)
                    packets_received += 1
                except socket.timeout:
                    continue
            
            elapsed = time.time() - start_time
            print(f"Recorded {packets_received} packets in {elapsed:.1f} seconds")
            print(f"WAV file saved to: {filename}")
            
        except Exception as e:
            print(f"Error recording at {rate} Hz: {e}")
        finally:
            wav_file.close()
    
    # Now let's play back each file
    print("\n\n=== PLAYBACK TEST ===")
    print("Listen to each file and choose the one that sounds correct (no chipmunk/slow effect)")
    
    p = pyaudio.PyAudio()
    
    for rate in sample_rates:
        filename = f"audio_diagnosis/test_{rate}hz_{timestamp}.wav"
        if not os.path.exists(filename):
            continue
        
        print(f"\nPlaying {rate} Hz recording...")
        wf = wave.open(filename, 'rb')
        
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                      channels=wf.getnchannels(),
                      rate=wf.getframerate(),
                      output=True)
        
        # Play for a few seconds
        data = wf.readframes(1024)
        start_time = time.time()
        end_time = start_time + 5  # Play 5 seconds max
        
        while data and time.time() < end_time:
            stream.write(data)
            data = wf.readframes(1024)
        
        stream.stop_stream()
        stream.close()
        wf.close()
        
        # Ask for feedback
        print("Did this sample rate sound correct? (y/n)")
        response = input().lower()
        if response.startswith('y'):
            print(f"\n=== RESULT ===")
            print(f"The detected correct sample rate is: {rate} Hz")
            print(f"UPDATE YOUR CODE WITH THIS SAMPLE RATE")
            break
    
    p.terminate()
    udp_sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='STM32 Sample Rate Detector')
    parser.add_argument('--port', type=int, default=6001, help='UDP listen port')
    parser.add_argument('--stm32', type=str, default='192.168.1.111', help='STM32 IP address')
    args = parser.parse_args()
    
    detect_sample_rate(
        listen_port=args.port,
        stm32_ip=args.stm32
    )
