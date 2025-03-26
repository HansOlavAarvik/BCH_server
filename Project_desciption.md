# IoT Electrical Cabinet Monitoring System

## Device Overview
I am working on an IoT device based on STM32H5 to monitor conditions within an electrical cabinet.

## Sensors
- Temperature inside and outside the cabinet
- Humidity inside and outside the cabinet
- Vibration (1KHz)
- Sound (32KHz mono)
- TOF, monitoring if the cabinet door is closed

## Feedback Components
- 3 LEDs (green, red and blue)
- Buzzer

## Connectivity
The IoT device is connected via ethernet and sends data through UDP. Currently using static IP, but will implement DHCP in the future. Temperature, humidity and TOF data is sent as JSON strings, while audio and vibration data are sent raw to reduce overhead.

## Server Responsibilities
- Record data and store it
- Play back audio (both streaming and stored data)
- Set alarm thresholds for the microcontroller
- Perform frequency analysis on audio and vibration data
- Plot data over time
- Provide UI for displaying data and accessing different functions

## Implementation Plan
The server will be written in Python. Currently, the server will run locally with static IPs for prototyping. The microcontroller code is mostly complete, so development will focus on the server side.