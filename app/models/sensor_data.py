"""                                                                          │ │
│ │ Data models for sensor data                                                  │ │
│ │ """                                                                          │ │
│ │ from datetime import datetime                                                │ │
│ │ from typing import Dict, List, Optional, Union                               │ │
│ │                                                                              │ │
│ │ from pydantic import BaseModel, Field                                        │ │
│ │                                                                              │ │
│ │                                                                              │ │
│ │ class TemperatureReading(BaseModel):                                         │ │
│ │     """Temperature reading from inside or outside the cabinet"""             │ │
│ │     value: float                                                             │ │
│ │     location: str = "inside"  # "inside" or "outside"                        │ │
│ │     timestamp: datetime = Field(default_factory=datetime.now)                │ │
│ │                                                                              │ │
│ │                                                                              │ │
│ │ class HumidityReading(BaseModel):                                            │ │
│ │     """Humidity reading from inside or outside the cabinet"""                │ │
│ │     value: float                                                             │ │
│ │     location: str = "inside"  # "inside" or "outside"                        │ │
│ │     timestamp: datetime = Field(default_factory=datetime.now)                │ │
│ │                                                                              │ │
│ │                                                                              │ │
│ │ class TOFReading(BaseModel):                                                 │ │
│ │     """Time-of-Flight sensor reading for door state"""                       │ │
│ │     distance: float  # Distance in mm                                        │ │
│ │     door_closed: bool  # True if door is closed                              │ │
│ │     timestamp: datetime = Field(default_factory=datetime.now)                │ │
│ │                                                                              │ │
│ │                                                                              │ │
│ │ class SensorDataPacket(BaseModel):                                           │ │
│ │     """Complete sensor data packet from the IoT device"""                    │ │
│ │     device_id: str                                                           │ │
│ │     temperature: Dict[str, float] = {}  # {"inside": value, "outside":       │ │
│ │ value}                                                                       │ │
│ │     humidity: Dict[str, float] = {}  # {"inside": value, "outside": value}   │ │
│ │     tof: Optional[TOFReading] = None                                         │ │
│ │     led_status: Dict[str, bool] = {}  # {"red": bool, "green": bool, "blue": │ │
│ │  bool}                                                                       │ │
│ │     buzzer_active: bool = False                                              │ │
│ │     timestamp: datetime = Field(default_factory=datetime.now)                │ │
│ │                                                                              │ │
│ │                                                                              │ │
│ │ class AudioMetadata(BaseModel):                                              │ │
│ │     """Metadata for audio recordings"""                                      │ │
│ │     device_id: str                                                           │ │
│ │     sample_rate: int = 32000  # 32KHz                                        │ │
│ │     duration_ms: int                                                         │ │
│ │     timestamp: datetime = Field(default_factory=datetime.now)                │ │
│ │     format: str = "raw"  # Format of the data                                │ │
│ │                                                                              │ │
│ │                                                                              │ │
│ │ class VibrationMetadata(BaseModel):                                          │ │
│ │     """Metadata for vibration recordings"""                                  │ │
│ │     device_id: str                                                           │ │
│ │     sample_rate: int = 1000  # 1KHz                                          │ │
│ │     duration_ms: int                                                         │ │
│ │     timestamp: datetime = Field(default_factory=datetime.now)                │ │
│ │     format: str = "raw"  # Format of the data                                │ │
│ │                                                                              │ │
│ │                                                                              │ │
│ │ class AlarmThresholds(BaseModel):                                            │ │
│ │     """Alarm thresholds for the IoT device"""                                │ │
│ │     temperature_max: Dict[str, float] = {"inside": 40.0, "outside": 40.0}    │ │
│ │     temperature_min: Dict[str, float] = {"inside": 5.0, "outside": -10.0}    │ │
│ │     humidity_max: Dict[str, float] = {"inside": 80.0, "outside": 100.0}      │ │
│ │     humidity_min: Dict[str, float] = {"inside": 20.0, "outside": 0.0}        │ │
│ │     door_open_alarm: bool = True                                             │ │
│ │     vibration_threshold: float = 1.0                                         │ │
│ │     sound_threshold: float = 90.0  # dB