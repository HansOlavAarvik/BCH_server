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
        try:
            # First try to parse as JSON
            json_data = json.loads(data.decode('utf-8'))
            logger.debug(f"Received JSON data from {addr}: {json_data}")
            
            if self.json_callback:
                self.json_callback(json_data, addr)
            
        except json.JSONDecodeError:
            # Not JSON, so it's probably raw binary data
            # Determine if it's audio or vibration based on packet size or headers
            # This is simplistic and would need to be adjusted based on actual data format
            
            if len(data) > 1000:  # Arbitrary distinction for demonstration
                logger.debug(f"Received audio data from {addr}: {len(data)} bytes")
                if self.audio_callback:
                    self.audio_callback(data, addr)
            else:
                logger.debug(f"Received vibration data from {addr}: {len(data)} bytes")
                if self.vibration_callback:
                    self.vibration_callback(data, addr)
        
        except Exception as e:
            logger.error(f"Error processing data from {addr}: {e}")


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