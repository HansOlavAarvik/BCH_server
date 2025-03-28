#!/usr/bin/env python3
"""
Main entry point for the BCH Server application.
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from fastapi.staticfiles import StaticFiles

from app.utils.udp_listener import UDPListener
from app.data.storage import MemoryStorage
from app.frontend.dashboard import create_dashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create global data storage
storage = MemoryStorage()

# UDP listener and handler setup
def handle_json_data(data, addr):
    """Handler for JSON formatted sensor data"""
    logger.info(f"JSON data from {addr}: {data}")
    storage.add_sensor_data(data)

def handle_audio_data(data, addr):
    """Handler for raw audio data"""
    logger.info(f"Audio data from {addr}: {len(data)} bytes")
    storage.add_audio_data(data, addr[0])

def handle_vibration_data(data, addr):
    """Handler for raw vibration data"""
    logger.info(f"Vibration data from {addr}: {len(data)} bytes")
    storage.add_vibration_data(data, addr[0])

# Setup UDP listener
udp_listener = UDPListener(
    port=3390,  # Updated port to match the STM32 data transmission
    json_callback=handle_json_data,
    audio_callback=handle_audio_data,
    vibration_callback=handle_vibration_data
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for FastAPI"""
    # Startup
    await udp_listener.start()
    logger.info("UDP listener started")
    
    yield
    
    # Shutdown
    udp_listener.stop()
    logger.info("UDP listener stopped")

# Create FastAPI app
app = FastAPI(
    title="BCH Server",
    description="IoT Electrical Cabinet Monitoring Server",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create Dash app
dash_app = create_dashboard(storage)

# Mount Dash app
from starlette.middleware.wsgi import WSGIMiddleware
app.mount("/dashboard", WSGIMiddleware(dash_app.server))

# API endpoints
@app.get("/", tags=["status"])
async def root():
    """Root endpoint - provides basic API status"""
    return {"status": "online", "message": "BCH Server API is running"}

@app.get("/api/sensors/latest", tags=["sensors"])
async def get_latest_sensor_data():
    """Get the latest sensor readings"""
    return storage.get_latest_sensor_data()

@app.get("/api/devices", tags=["devices"])
async def get_connected_devices():
    """Get list of connected devices"""
    return storage.get_connected_devices()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)