#!/usr/bin/env python3
"""
Basic example of using the UltravoxClient to create and interact with a call.
"""

import asyncio
import logging
import os
from typing import Dict, Any

from ultravox_client import UltravoxClient

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def handle_calculator_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example tool handler for a calculator tool.

    Args:
        parameters: The tool parameters

    Returns:
        The calculation result
    """
    operation = parameters.get("operation")
    a = float(parameters.get("a", 0))
    b = float(parameters.get("b", 0))

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return {"result": result}


async def main() -> None:
    """Main function to demonstrate UltravoxClient usage."""
    # Get API key from environment variable
    api_key = os.environ.get("ULTRAVOX_API_KEY")
    if not api_key:
        raise ValueError("ULTRAVOX_API_KEY environment variable not set")

    # Initialize the client
    client = UltravoxClient(api_key=api_key)

    try:
        # List available voices
        voices = await client.voices.list()
        logging.info(f"Available voices: {voices}")

        # Create a new call
        call = await client.calls.create(
            system_prompt=(
                "You are a helpful assistant with access to a calculator tool."
            ),
            voice="claude",  # Replace with an actual voice ID from the voices list
            selected_tools=[
                {"name": "calculator"}
            ],  # Reference to a tool we'll register later
        )
        logging.info(f"Created call with ID: {call['id']}")

        # Join the call via WebSocket
        session = await client.join_call(call["id"])

        # Register event handlers
        session.on(
            "state", lambda state: logging.info(f"Call state changed to: {state}")
        )
        session.on(
            "output",
            lambda text, final: logging.info(f"Agent output: {text} (final: {final})"),
        )
        session.on("error", lambda error: logging.error(f"Error: {error}"))
        session.on("ended", lambda: logging.info("Call ended"))

        # Register the calculator tool
        session.register_tool("calculator", handle_calculator_tool)

        # Start the session
        await session.start()

        # Wait for some time to allow interaction
        logging.info("Session started. Press Ctrl+C to stop...")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logging.info("Stopping session...")

        # Stop the session
        await session.stop()

    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        # Ensure we close any remaining sessions
        if "session" in locals():
            await session.stop()


if __name__ == "__main__":
    asyncio.run(main())
