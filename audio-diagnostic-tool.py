import numpy as np
import matplotlib.pyplot as plt
import wave
import pyaudio
import struct
import os
import sys

def analyze_wav_file(filename):
    """Analyze a WAV file and display diagnostic information"""
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found")
        return False
    
    try:
        # Open the WAV file
        with wave.open(filename, 'rb') as wf:
            # Get basic info
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / framerate
            
            # Print file information
            print(f"\n{'='*50}")
            print(f"WAV File Analysis: {filename}")
            print(f"{'='*50}")
            print(f"Channels: {channels}")
            print(f"Sample Width: {sample_width} bytes ({sample_width*8} bits)")
            print(f"Sample Rate: {framerate} Hz")
            print(f"Number of Frames: {n_frames}")
            print(f"Duration: {duration:.2f} seconds")
            
            # Read the first chunk of audio data for analysis
            max_frames_to_analyze = min(framerate * 5, n_frames)  # At most 5 seconds
            wf.setpos(0)
            audio_data = wf.readframes(max_frames_to_analyze)
            
            # Convert to numpy array based on sample width
            if sample_width == 1:
                # 8-bit is unsigned
                samples = np.frombuffer(audio_data, dtype=np.uint8)
                samples = samples.astype(np.float32) / 128.0 - 1.0
            elif sample_width == 2:
                # 16-bit is signed
                samples = np.frombuffer(audio_data, dtype=np.int16)
                samples = samples.astype(np.float32) / 32768.0
            elif sample_width == 3:
                # 24-bit requires special handling (convert to 32-bit)
                samples = np.zeros(len(audio_data) // 3, dtype=np.int32)
                for i in range(len(samples)):
                    # Extract the 3 bytes and convert to 32-bit signed integer
                    if i*3+2 < len(audio_data):
                        sample = audio_data[i*3] | (audio_data[i*3+1] << 8) | (audio_data[i*3+2] << 16)
                        # Sign extend if negative
                        if sample & 0x800000:
                            sample |= 0xFF000000
                        samples[i] = sample
                samples = samples.astype(np.float32) / 8388608.0  # 2^23
            elif sample_width == 4:
                # 32-bit is signed
                samples = np.frombuffer(audio_data, dtype=np.int32)
                samples = samples.astype(np.float32) / 2147483648.0  # 2^31
            
            # Separate channels if needed
            if channels > 1:
                channel_samples = []
                for i in range(channels):
                    channel_samples.append(samples[i::channels])
                samples = channel_samples[0]  # Just analyze the first channel for simplicity
            
            # Basic statistics
            print(f"\nAudio Statistics:")
            print(f"Min value: {np.min(samples):.6f}")
            print(f"Max value: {np.max(samples):.6f}")
            print(f"Mean: {np.mean(samples):.6f}")
            print(f"RMS: {np.sqrt(np.mean(samples**2)):.6f}")
            
            # Check for potential issues
            if np.max(np.abs(samples)) < 0.01:
                print("\nWarning: Audio levels are very low (< 1% of maximum)")
            
            if np.max(np.abs(samples)) > 0.99:
                print("Warning: Audio levels are near maximum, possible clipping")
            
            zero_crossings = np.sum(np.diff(np.signbit(samples)))
            expected_crossings = duration * 1000  # Rough estimate - expect at least 1000 crossings/sec for typical audio
            if zero_crossings < expected_crossings:
                print(f"Warning: Low number of zero crossings ({zero_crossings}), audio might be DC-biased or corrupted")
            
            # Count consecutive identical samples (could indicate dropouts)
            consecutive_count = 0
            max_consecutive = 0
            prev_sample = None
            for sample in samples:
                if sample == prev_sample:
                    consecutive_count += 1
                else:
                    max_consecutive = max(max_consecutive, consecutive_count)
                    consecutive_count = 1
                prev_sample = sample
            
            max_consecutive = max(max_consecutive, consecutive_count)
            if max_consecutive > 100:
                print(f"Warning: Found {max_consecutive} consecutive identical samples, possible dropouts or silence")
            
            # Plot the data
            plt.figure(figsize=(12, 8))
            
            # Waveform
            plt.subplot(3, 1, 1)
            plot_frames = min(10000, len(samples))  # Plot at most 10000 samples for visibility
            plt.plot(samples[:plot_frames])
            plt.title('Audio Waveform (first 10000 samples)')
            plt.xlabel('Sample Index')
            plt.ylabel('Amplitude')
            plt.grid(True)
            
            # Histogram
            plt.subplot(3, 1, 2)
            plt.hist(samples, bins=100, alpha=0.7)
            plt.title('Amplitude Distribution')
            plt.xlabel('Amplitude')
            plt.ylabel('Frequency')
            plt.grid(True)
            
            # Spectrogram
            plt.subplot(3, 1, 3)
            plt.specgram(samples, Fs=framerate, NFFT=1024, noverlap=512)
            plt.title('Spectrogram')
            plt.xlabel('Time (s)')
            plt.ylabel('Frequency (Hz)')
            
            plt.tight_layout()
            plt.savefig(f"{os.path.splitext(filename)[0]}_analysis.png")
            plt.show()
            
            return True
    
    except Exception as e:
        print(f"Error analyzing WAV file: {e}")
        return False

def play_wav_file(filename):
    """Play a WAV file using PyAudio for direct hardware playback"""
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found")
        return
    
    try:
        # Open the WAV file
        wf = wave.open(filename, 'rb')
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        # Define callback function for streaming
        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            return (data, pyaudio.paContinue)
        
        # Open stream using callback
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        stream_callback=callback)
        
        # Start the stream
        stream.start_stream()
        
        print(f"Playing {filename}... Press Ctrl+C to stop.")
        
        # Wait for stream to finish
        while stream.is_active():
            import time
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("Playback stopped by user")
    except Exception as e:
        print(f"Error playing WAV file: {e}")
    finally:
        # Clean up
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        if 'p' in locals():
            p.terminate()
        if 'wf' in locals():
            wf.close()

def try_alternative_formats(filename):
    """Try different format interpretations of the audio data"""
    if not os.path.exists(filename):
        print(f"Error: File {filename} not found")
        return
    
    try:
        # Read the raw data first
        with open(filename, 'rb') as f:
            raw_data = f.read()
        
        # Create temporary WAV files with different formats
        sample_rates = [32000, 44100, 48000]
        formats = [
            {'name': 'original', 'convert': lambda x: x},
            {'name': 'swap_endian16', 'convert': lambda x: swap_endianness_16bit(x)},
            {'name': 'swap_endian24', 'convert': lambda x: swap_endianness_24bit(x)},
            {'name': 'pcm_s24le', 'convert': lambda x: convert_24bit_to_32bit(x)}
        ]
        
        for rate in sample_rates:
            for fmt in formats:
                try:
                    # Create a new filename
                    new_filename = f"{os.path.splitext(filename)[0]}_{fmt['name']}_{rate}hz.wav"
                    
                    # Create a new WAV file with current format interpretation
                    converted_data = fmt['convert'](raw_data)
                    
                    # Determine appropriate sample width
                    if fmt['name'] == 'pcm_s24le':
                        sample_width = 4  # 32-bit output
                    else:
                        sample_width = 3  # 24-bit
                    
                    with wave.open(new_filename, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(sample_width)
                        wf.setframerate(rate)
                        wf.writeframes(converted_data)
                    
                    print(f"Created {new_filename}")
                except Exception as e:
                    print(f"Error creating {fmt['name']} format at {rate}Hz: {e}")
        
        print("\nCreated multiple WAV files with different format interpretations.")
        print("Try playing each one to see which sounds correct.")
    
    except Exception as e:
        print(f"Error processing file: {e}")

def swap_endianness_16bit(data):
    """Swap endianness for 16-bit samples in byte array"""
    # Ensure even length
    if len(data) % 2 != 0:
        data = data[:-1]
    
    result = bytearray(len(data))
    for i in range(0, len(data), 2):
        result[i] = data[i+1]
        result[i+1] = data[i]
    
    return bytes(result)

def swap_endianness_24bit(data):
    """Swap endianness for 24-bit samples in byte array"""
    # Ensure length is multiple of 3
    remainder = len(data) % 3
    if remainder != 0:
        data = data[:-remainder]
    
    result = bytearray(len(data))
    for i in range(0, len(data), 3):
        result[i] = data[i+2]
        result[i+1] = data[i+1]
        result[i+2] = data[i]
    
    return bytes(result)

def convert_24bit_to_32bit(data):
    """Convert 24-bit PCM data to 32-bit PCM with proper sign extension"""
    # Ensure length is multiple of 3
    remainder = len(data) % 3
    if remainder != 0:
        data = data[:-remainder]
    
    # Create buffer for 32-bit data (4 bytes per sample)
    result = bytearray(len(data) // 3 * 4)
    
    for i in range(len(data) // 3):
        # Extract 3 bytes (24-bit sample)
        byte0 = data[i*3]
        byte1 = data[i*3+1]
        byte2 = data[i*3+2]
        
        # Convert to a signed integer
        value = byte0 | (byte1 << 8) | (byte2 << 16)
        
        # Sign extend if needed
        if value & 0x800000:
            value |= 0xFF000000
        
        # Pack as 32-bit little-endian
        result[i*4] = value & 0xFF
        result[i*4+1] = (value >> 8) & 0xFF
        result[i*4+2] = (value >> 16) & 0xFF
        result[i*4+3] = (value >> 24) & 0xFF
    
    return bytes(result)

def main():
    if len(sys.argv) < 2:
        print("Usage: python audio_diagnostic.py <wav_file> [action]")
        print("Actions:")
        print("  analyze - Analyze audio file (default)")
        print("  play - Play audio file")
        print("  fix - Try different format interpretations")
        return
    
    filename = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "analyze"
    
    if action == "analyze":
        analyze_wav_file(filename)
    elif action == "play":
        play_wav_file(filename)
    elif action == "fix":
        try_alternative_formats(filename)
    else:
        print(f"Unknown action: {action}")

if __name__ == "__main__":
    main()
