"""
Memory-based storage for sensor data, audio, and vibration data.
This is a simple implementation for the prototype - 
would be replaced with database storage in a production system.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
from collections import deque

logger = logging.getLogger(__name__)

class MemoryStorage:
    """
    In-memory storage for sensor data, audio, and vibration.
    """
    def __init__(self, max_samples=1000):
        """
        Initialize storage with maximum sample limits.
        """
        self.max_samples = max_samples
        self.sensor_data = deque(maxlen=max_samples)
        self.audio_data = {}  # Dict by device_id
        self.vibration_data = {}  # Dict by device_id
        self.connected_devices = set()
        self.latest_data = {}  # Latest data by device_id
    
    def add_sensor_data(self, data):
        """
        Add JSON sensor data to storage.
        """
        timestamp = datetime.now().isoformat()
        
        # Ensure data has device_id
        if "device_id" not in data:
            logger.warning("Received sensor data without device_id")
            return
        
        device_id = data["device_id"]
        self.connected_devices.add(device_id)
        
        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = timestamp
        
        # Store data
        self.sensor_data.append(data)
        self.latest_data[device_id] = data
        logger.debug(f"Added sensor data for device {device_id}")
    
    def add_audio_data(self, data: bytes, device_ip: str):
        """
        Add raw audio data to storage.
        For the prototype, we just store the most recent sample per device.
        """
        device_id = f"device_{device_ip}"  # Simple mapping for prototype
        self.connected_devices.add(device_id)
        
        # Store data (just most recent for prototype)
        if device_id not in self.audio_data:
            self.audio_data[device_id] = deque(maxlen=10)  # Keep last 10 samples
            
        timestamp = datetime.now().isoformat()
        self.audio_data[device_id].append({
            "timestamp": timestamp,
            "size": len(data),
            "data": data  # In production, might store to file/DB
        })
        logger.debug(f"Added {len(data)} bytes of audio data for {device_id}")
    
    def add_vibration_data(self, data: bytes, device_ip: str):
        """
        Add raw vibration data to storage.
        For the prototype, we just store the most recent sample per device.
        """
        device_id = f"device_{device_ip}"  # Simple mapping for prototype
        self.connected_devices.add(device_id)
        
        # Store data (just most recent for prototype)
        if device_id not in self.vibration_data:
            self.vibration_data[device_id] = deque(maxlen=50)  # Keep last 50 samples
            
        timestamp = datetime.now().isoformat()
        self.vibration_data[device_id].append({
            "timestamp": timestamp,
            "size": len(data),
            "data": data  # In production, might store to file/DB
        })
        logger.debug(f"Added {len(data)} bytes of vibration data for {device_id}")
    
    def get_latest_sensor_data(self):
        """
        Get the latest sensor data for all devices.
        """
        logger.info(f"Returning latest data: {self.latest_data}")
        return self.latest_data
    
    def get_sensor_history(self, device_id=None, limit=100):
        """
        Get sensor data history for a specific device or all devices.
        """
        if device_id:
            # Filter by device_id
            history = [d for d in self.sensor_data if d.get("device_id") == device_id]
            return list(history[-limit:])
        else:
            # Return all devices' data
            return list(self.sensor_data)[-limit:]
    
    def get_connected_devices(self):
        """
        Get list of connected devices.
        """
        result = []
        for device_id in self.connected_devices:
            has_sensor = device_id in self.latest_data
            has_audio = device_id in self.audio_data and len(self.audio_data[device_id]) > 0
            has_vibration = device_id in self.vibration_data and len(self.vibration_data[device_id]) > 0
            
            result.append({
                "device_id": device_id,
                "has_sensor_data": has_sensor,
                "has_audio_data": has_audio,
                "has_vibration_data": has_vibration,
                "last_seen": self.latest_data.get(device_id, {}).get("timestamp", None)
            })
        
        return result