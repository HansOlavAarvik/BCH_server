#!/usr/bin/env python3
"""
Main entry point for the BCH Server application.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="BCH Server",
    description="IoT Electrical Cabinet Monitoring Server",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Import API routers
# from app.api.sensors import router as sensors_router
# from app.api.audio import router as audio_router
# from app.api.analysis import router as analysis_router

# Add API routers
# app.include_router(sensors_router, prefix="/api/sensors", tags=["sensors"])
# app.include_router(audio_router, prefix="/api/audio", tags=["audio"])
# app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])

@app.get("/", tags=["status"])
async def root():
    """
    Root endpoint - provides basic API status
    """
    return {"status": "online", "message": "BCH Server API is running"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)