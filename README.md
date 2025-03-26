# BCH Server

IoT Electrical Cabinet Monitoring Server for collecting, analyzing, and visualizing sensor data from STM32-based IoT devices.

## Features

- Receives UDP data from STM32H5-based IoT devices
- Processes sensor data: temperature, humidity, vibration, sound, TOF
- Performs frequency analysis on vibration and audio data
- Provides real-time visualization via Dash frontend
- REST API via FastAPI

## Setup

```bash
# Install dependencies
poetry install

# Start server
poetry run python -m app.main
```

## Architecture

- `/app/` - Main application directory
  - `/api/` - FastAPI endpoints
  - `/frontend/` - Dash visualization
  - `/data/` - Data storage and management
  - `/models/` - Pydantic data models
  - `/utils/` - Utility functions
  
## Testing

UDP data can be tested with the included Hello_from_stm.py script.