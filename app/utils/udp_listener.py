"""
UDP Listener for receiving data from STM32 IoT devices
"""
import asyncio
import json
import logging
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)

class UDPListener:
    """
    Listens for UDP packets from IoT devices and processes them accordingly.
    Handles both JSON data (temperature, humidity, TOF) and raw data (audio, vibration).
    """
    def __init__(
        self, 
        host: str = "0.0.0.0", 
        port: int = 9000,
        json_callback: Optional[Callable] = None,
        audio_callback: Optional[Callable] = None,
        vibration_callback: Optional[Callable] = None
    ):
        self.host = host
        self.port = port
        self.json_callback = json_callback
        self.audio_callback = audio_callback
        self.vibration_callback = vibration_callback
        self.transport = None
        self.protocol = None
        self.is_running = False

    async def start(self):
        """Start the UDP listener"""
        loop = asyncio.get_running_loop()
        self.transport, self.protocol = await loop.create_datagram_endpoint(
            lambda: UDPProtocol(self._process_data),
            local_addr=(self.host, self.port)
        )
        self.is_running = True
        logger.info(f"UDP listener started on {self.host}:{self.port}")

    def stop(self):
        """Stop the UDP listener"""
        if self.transport:
            self.transport.close()
            self.transport = None
            self.protocol = None
            self.is_running = False
            logger.info("UDP listener stopped")

    def _process_data(self, data: bytes, addr):
        """
        Process received UDP data
        
        This method tries to determine if the data is JSON or raw binary data
        and routes it to the appropriate callback.
        """
        logger.info(f"Received data from {addr}, {len(data)} bytes")
        
        try:
            # First try to parse as JSON
            try:
                decoded = data.decode('utf-8')
                logger.info(f"Decoded data: {decoded[:100]}...")
                json_data = json.loads(decoded)
                logger.info(f"Received JSON data from {addr}: {json_data}")
                
                # Transform the STM32 sensor data format to our internal format
                if "Inside_temperature" in json_data:
                    # This is the STM32 sensor data format
                    processed_data = {
                        "device_id": f"device_{addr[0]}",
                        "temperature": {
                            "inside": json_data.get("Inside_temperature", 0),
                            "outside": json_data.get("Outside_temperature", 0)
                        },
                        "humidity": {
                            "inside": json_data.get("Inside_humidity", 0),
                            "outside": json_data.get("outisde_humidity", 0)  # Note the typo in the key
                        },
                        "tof": {
                            "distance": json_data.get("Time_of_flight", 0),
                            "door_closed": json_data.get("Time_of_flight", 0) < -450  # Example door threshold
                        }
                    }
                    logger.info(f"Processed STM32 sensor data: {processed_data}")
                    
                    if self.json_callback:
                        self.json_callback(processed_data, addr)
                    else:
                        logger.warning("No JSON callback registered")
                else:
                    # This is some other JSON format, pass it through as-is
                    if self.json_callback:
                        self.json_callback(json_data, addr)
                    else:
                        logger.warning("No JSON callback registered")
                
            except json.JSONDecodeError as je:
                logger.info(f"Not valid JSON: {je}")
                # Not JSON, so it's probably raw binary data
                # Determine if it's audio or vibration based on packet size or headers
                # This is simplistic and would need to be adjusted based on actual data format
                
                if len(data) > 1000:  # Arbitrary distinction for demonstration
                    logger.info(f"Received audio data from {addr}: {len(data)} bytes")
                    if self.audio_callback:
                        self.audio_callback(data, addr)
                    else:
                        logger.warning("No audio callback registered")
                else:
                    logger.info(f"Received vibration data from {addr}: {len(data)} bytes")
                    if self.vibration_callback:
                        self.vibration_callback(data, addr)
                    else:
                        logger.warning("No vibration callback registered")
            
        except Exception as e:
            logger.error(f"Error processing data from {addr}: {e}")
            import traceback
            logger.error(traceback.format_exc())


class UDPProtocol(asyncio.DatagramProtocol):
    """
    UDP protocol implementation for asyncio
    """
    def __init__(self, data_callback: Callable):
        self.data_callback = data_callback
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        """Called when a UDP packet is received"""
        self.data_callback(data, addr)

    def error_received(self, exc):
        """Called when a send or receive operation raises an OSError"""
        logger.error(f"UDP protocol error: {exc}")