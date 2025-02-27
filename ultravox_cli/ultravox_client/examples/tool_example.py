#!/usr/bin/env python3
"""
Example of using the ToolRegistry to register and execute tools.
"""

import asyncio
import logging
import os
from typing import Dict, Any

from ultravox_client import UltravoxClient
from ultravox_client.tools import ToolRegistry

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create a tool registry
registry = ToolRegistry()


# Define a calculator tool
async def calculator(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculator tool that performs basic arithmetic operations.

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


# Define a weather tool
async def weather(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Weather tool that returns the weather for a location.

    Args:
        parameters: The tool parameters

    Returns:
        The weather information
    """
    location = parameters.get("location")

    # In a real implementation, this would call a weather API
    # For this example, we'll just return mock data
    return {
        "location": location,
        "temperature": 72,
        "conditions": "sunny",
        "humidity": 45,
    }


async def main() -> None:
    """Main function to demonstrate ToolRegistry usage."""
    # Register the calculator tool
    registry.register(
        name="calculator",
        handler=calculator,
        description="Performs basic arithmetic operations",
        parameters={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The operation to perform",
                },
                "a": {
                    "type": "number",
                    "description": "The first operand",
                },
                "b": {
                    "type": "number",
                    "description": "The second operand",
                },
            },
            "required": ["operation", "a", "b"],
        },
    )

    # Register the weather tool
    registry.register(
        name="weather",
        handler=weather,
        description="Gets the weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get weather for",
                },
            },
            "required": ["location"],
        },
    )

    # List all registered tools
    tools = registry.list_tools()
    logging.info(f"Registered tools: {tools}")

    # Execute the calculator tool
    calc_result = await registry.execute_tool(
        "calculator", {"operation": "add", "a": 5, "b": 3}
    )
    logging.info(f"Calculator result: {calc_result}")

    # Execute the weather tool
    weather_result = await registry.execute_tool(
        "weather", {"location": "San Francisco"}
    )
    logging.info(f"Weather result: {weather_result}")

    # Get API key from environment variable
    api_key = os.environ.get("ULTRAVOX_API_KEY")
    if not api_key:
        logging.warning(
            "ULTRAVOX_API_KEY environment variable not set, skipping client example"
        )
        return

    # Initialize the client
    client = UltravoxClient(api_key=api_key)

    try:
        # Create a new call with the registered tools
        call = await client.calls.create(
            system_prompt="You are a helpful assistant with access to calculator and weather tools.",
            voice="claude",  # Replace with an actual voice ID
            selected_tools=[
                {"name": "calculator"},
                {"name": "weather"},
            ],
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

        # Register the tools with the session
        session.register_tool("calculator", calculator)
        session.register_tool("weather", weather)

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
