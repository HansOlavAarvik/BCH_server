import socket
import struct
import numpy as np
import argparse
import time
import wave
import os

def record_to_wav(listen_port=6001, stm32_ip="192.168.1.111", 
                 sample_rate=int(32018), duration=5):
    """
    Records UDP audio stream directly to WAV file for analysis
    """
    # Create output directory
    if not os.path.exists("audio_analysis"):
        os.makedirs("audio_analysis")
    
    # Generate filename with timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"audio_analysis/stm32_audio_{timestamp}.wav"
    
    print(f"\n=== AUDIO RECORDER ===")
    print(f"Target device: {stm32_ip}")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Recording duration: {duration} seconds")
    print(f"Output file: {filename}")
    print("=====================\n")
    
    # Socket setup
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(("0.0.0.0", listen_port))
    udp_sock.settimeout(0.1)
    
    # WAV file setup
    wav_file = wave.open(filename, 'wb')
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)
    
    # Variables for data collection
    all_samples = []
    start_time = time.time()
    end_time = start_time + duration
    packets_received = 0
    
    print(f"Waiting for audio stream from {stm32_ip}...")
    print(f"Recording for {duration} seconds...")
    
    try:
        while time.time() < end_time:
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
                
                # Write directly to WAV file
                wav_file.writeframes(data)
                
                # Also accumulate for analysis
                samples = np.frombuffer(data, dtype=np.int16)
                all_samples.extend(samples)
                
                packets_received += 1
                
                # Print progress
                elapsed = time.time() - start_time
                remaining = max(0, duration - elapsed)
                if packets_received % 100 == 0:
                    print(f"Received {packets_received} packets. {remaining:.1f}s remaining...")
            
            except socket.timeout:
                # Just a timeout, continue
                continue
        
        # Recording complete
        elapsed = time.time() - start_time
        print(f"\nRecording complete: {packets_received} packets in {elapsed:.1f}s")
        print(f"Captured {len(all_samples)} samples")
        
        # Basic audio analysis
        if all_samples:
            samples_array = np.array(all_samples)
            print("\n=== AUDIO ANALYSIS ===")
            print(f"Min value: {np.min(samples_array)}")
            print(f"Max value: {np.max(samples_array)}")
            print(f"Mean value: {np.mean(samples_array):.2f}")
            print(f"RMS level: {np.sqrt(np.mean(samples_array**2)):.2f}")
            print(f"Zero crossings: {np.sum(np.diff(np.signbit(samples_array)))}")
            
            # Check for discontinuities (potential cause of crackling)
            diffs = np.abs(np.diff(samples_array))
            large_jumps = np.sum(diffs > 5000)  # Threshold for "large" jumps
            print(f"Large amplitude jumps: {large_jumps} ({large_jumps/len(diffs)*100:.2f}%)")
            
            # Plot spectrum if matplotlib is available
            try:
                import matplotlib.pyplot as plt
                from scipy import signal
                
                # Compute spectrum
                f, Pxx = signal.welch(samples_array, fs=sample_rate, nperseg=1024)
                
                # Plot spectrum
                plt.figure(figsize=(10, 6))
                plt.semilogy(f, Pxx)
                plt.xlabel('Frequency [Hz]')
                plt.ylabel('PSD [V**2/Hz]')
                plt.title('Audio Spectrum Analysis')
                plt.grid(True)
                spectrum_file = f"audio_analysis/spectrum_{timestamp}.png"
                plt.savefig(spectrum_file)
                print(f"Spectrum saved to {spectrum_file}")
                
                # Plot waveform
                plt.figure(figsize=(12, 6))
                plt.plot(samples_array[:min(len(samples_array), 10000)])
                plt.title('Audio Waveform (first 10,000 samples)')
                plt.xlabel('Sample')
                plt.ylabel('Amplitude')
                plt.grid(True)
                waveform_file = f"audio_analysis/waveform_{timestamp}.png"
                plt.savefig(waveform_file)
                print(f"Waveform saved to {waveform_file}")
                
            except ImportError:
                print("Matplotlib/SciPy not available for spectrum analysis")
        
        print(f"\nWAV file saved to: {filename}")
        print("Play this file with any audio player to check the quality")
        
    finally:
        wav_file.close()
        udp_sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='STM32 UDP Audio Recorder')
    parser.add_argument('--port', type=int, default=6001, help='UDP listen port')
    parser.add_argument('--stm32', type=str, default='192.168.1.111', help='STM32 IP address')
    parser.add_argument('--rate', type=int, default=int(32018), help='Audio sample rate (Hz)')
    parser.add_argument('--duration', type=int, default=5, help='Recording duration (seconds)')
    args = parser.parse_args()
    
    record_to_wav(
        listen_port=args.port,
        stm32_ip=args.stm32,
        sample_rate=args.rate,
        duration=args.duration
    )
