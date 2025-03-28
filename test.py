#!/usr/bin/env python3
"""
Test script to send simulated STM32 data packets to the UDP server
"""
import socket
import json
import time
from datetime import datetime

def send_test_data(host="127.0.0.1", port=6002):
    """
    Send test data to the UDP server
    """
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Create a sample JSON packet that matches the expected format
    test_data = {
        "device_id": "stm32_test_device",
        "temperature": {
            "inside": 25.5,
            "outside": 18.2
        },
        "humidity": {
            "inside": 45.0,
            "outside": 65.0
        },
        "tof": {
            "distance": 250.0,
            "door_closed": True
        },
        "led_status": {
            "red": False,
            "green": True,
            "blue": False
        },
        "buzzer_active": False,
        "timestamp": datetime.now().isoformat()
    }
    
    # Convert to JSON string and encode to bytes
    json_data = json.dumps(test_data)
    data_bytes = json_data.encode('utf-8')
    
    print(f"Sending test data to {host}:{port}")
    print(f"Data: {json_data}")
    
    # Send data
    sock.sendto(data_bytes, (host, port))
    print("Data sent!")
    
    # Close socket
    sock.close()

if __name__ == "__main__":
    # Send 5 packets with a 2-second delay
    for i in range(5):
        send_test_data()
        print(f"Sent packet {i+1}/5")
        time.sleep(2)