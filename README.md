# BCH Server

IoT Electrical Cabinet Monitoring Server for collecting, analyzing, and visualizing sensor data from STM32-based IoT devices.

## Features

- Receives UDP data from STM32H5-based IoT devices
- Processes sensor data: temperature, humidity, vibration, sound, TOF
- Performs frequency analysis on vibration and audio data (coming soon)
- Provides real-time visualization via Dash frontend
- REST API via FastAPI

## Minimal Prototype

The current implementation is a minimal working prototype with the following features:
- UDP data reception (JSON and raw audio/vibration)
- In-memory data storage
- Basic visualization dashboard
- Simple REST API endpoints

## Setup

For the prototype, you'll need Python 3.12+ and Poetry installed.

```bash
# Install dependencies
poetry install

# Start server
poetry run python -m app.main
```

### System Dependencies

For audio playback (optional), you'll need to install additional system packages:

```bash
# Ubuntu/Debian
sudo apt-get install python3-dev portaudio19-dev

# Then enable PyAudio in pyproject.toml by uncommenting the line
# And run: poetry install
```

Then:
1. Open http://localhost:8000/ for the API
2. Open http://localhost:8000/dashboard/ for the visualization dashboard

## Testing

You can test the server with the following tools:

### 1. JSON Sensor Data

Run the UDP test client to simulate JSON sensor data:

```bash
python Hello_from_stm.py
```

In another terminal, send a sample UDP message:

```bash
echo '{"device_id": "stm001", "temperature": {"inside": 25.4, "outside": 18.2}, "humidity": {"inside": 45.6, "outside": 72.1}, "tof": {"distance": 124.5, "door_closed": true}}' | nc -u localhost 6002
```

### 2. Audio Data Testing

For audio streaming test:

```bash
python simple-reliable-receiver.py
```

## Architecture

- `/app/` - Main application directory
  - `/api/` - FastAPI endpoints
  - `/frontend/` - Dash visualization
  - `/data/` - Data storage and management
  - `/models/` - Pydantic data models
  - `/utils/` - Utility functions

## Future Enhancements

- Database storage for sensor data
- Frequency analysis for audio and vibration
- Alarms and notifications
- Data download and export
- Communication back to the microcontroller