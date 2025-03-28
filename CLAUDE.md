# BCH_Server Development Guidelines

## Run Commands
- Run the main server (includes UDP receiver): `python -m app.main`
- Run standalone UDP message receiver (for testing): `python Hello_from_stm.py`
- Run audio streaming: `python simple-reliable-receiver.py`
- Run with custom port: `python simple-reliable-receiver.py --port 3391`
- Run with specified device: `python simple-reliable-receiver.py --stm32 192.168.1.111`

## Code Style Guidelines
- **Imports**: Standard library imports first, then third-party packages, then local modules
- **Naming**: Use snake_case for variables/functions, PascalCase for classes
- **Docstrings**: Use triple quotes with parameter descriptions
- **Error handling**: Use try/except blocks with specific exceptions and error messages
- **Threading**: Use daemon threads for background tasks, ensure proper cleanup
- **IP/Port Configuration**: Use command line arguments with sensible defaults
- **Function Design**: Prioritize functions with clear single responsibility
- **Comments**: Include explanatory comments for complex operations
- **Type Hints**: Add type annotations for function parameters and returns
- **Constants**: Define port numbers and IP addresses as configurable parameters

## Dependencies
- socket, struct, numpy, pyaudio, argparse, threading, queue