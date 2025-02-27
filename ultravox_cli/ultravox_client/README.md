# UltravoxClient

A Python client for the Ultravox API, providing a clean and intuitive interface for interacting with Ultravox's voice AI services.

## Installation

```bash
pip install ultravox_client
```

## Features

- Asynchronous API for efficient network operations
- Comprehensive coverage of Ultravox API endpoints
- WebSocket support for real-time voice interactions
- Type hints for better IDE integration and code safety

## Quick Start

```python
import asyncio
from ultravox_client import UltravoxClient

async def main():
    # Initialize the client with your API key
    client = UltravoxClient(api_key="your_api_key")

    # List available voices
    voices = await client.voices.list()
    print(f"Available voices: {voices}")

    # Create a new call
    call = await client.calls.create(
        system_prompt="You are a helpful assistant.",
        voice="claude"
    )
    print(f"Created call with ID: {call['id']}")

    # Join the call via WebSocket
    session = await client.join_call(call["id"])

    # Register event handlers
    session.on("state", lambda state: print(f"Call state changed to: {state}"))
    session.on("output", lambda text, final: print(f"Agent output: {text} (final: {final})"))

    # Start the session
    await session.start()

    # Wait for some time
    await asyncio.sleep(10)

    # Stop the session
    await session.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## API Documentation

### UltravoxClient

The main client class that provides access to all Ultravox API endpoints.

```python
client = UltravoxClient(api_key="your_api_key")
```

### Calls API

Methods for managing Ultravox calls:

- `list()` - List all calls
- `get(call_id)` - Get a specific call
- `create(system_prompt, temperature, voice, selected_tools, initial_messages, medium)` - Create a new call
- `get_messages(call_id)` - Get messages for a call
- `get_tools(call_id)` - Get tools for a call
- `get_recording(call_id)` - Get recording for a call

### Tools API

Methods for managing Ultravox tools:

- `list()` - List all tools
- `get(tool_id)` - Get a specific tool
- `create(name, description, parameters, handler)` - Create a new tool
- `update(tool_id, name, description, parameters, handler)` - Update a tool
- `delete(tool_id)` - Delete a tool

### Voices API

Methods for managing Ultravox voices:

- `list()` - List all voices
- `get(voice_id)` - Get a specific voice
- `create_clone(name, description, audio_url)` - Create a new voice clone
- `delete(voice_id)` - Delete a voice

### WebsocketSession

A class for real-time interaction with Ultravox calls via WebSocket:

- `start()` - Start the session
- `stop()` - Stop the session
- `register_tool(tool_name, handler)` - Register a handler for a client tool

## License

MIT
