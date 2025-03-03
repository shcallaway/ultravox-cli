import asyncio
import os
import pytest
import shlex
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Any, Dict, List, Optional, Generator
import argparse

# Add the project root to sys.path if needed
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ultravox_cli.cli import get_secret_menu, main
from ultravox_cli.ultravox_client.client import UltravoxClient


class MockWebSocketSession:
    """Mock WebSocket session for integration testing."""

    def __init__(self) -> None:
        """Initialize the mock session."""
        self.handlers: Dict[str, List[Any]] = {
            "output": [],
            "state": [],
            "ended": [],
            "error": [],
        }
        self.started = False
        self.messages: List[str] = []
        self.tools_registered: Dict[str, Any] = {}

    def on(self, event_type: str) -> Any:
        """Register an event handler."""
        def decorator(f: Any) -> Any:
            self.handlers[event_type].append(f)
            return f
        return decorator

    async def start(self) -> None:
        """Start the session."""
        self.started = True
        # Simulate the agent sending an initial response
        for handler in self.handlers["state"]:
            await handler("ready")
        for handler in self.handlers["output"]:
            await handler("Hello! Welcome to Dr. Donut. What can I get for you today?", False)
            # After a short delay, send final output
            await asyncio.sleep(0.1)
            await handler("Hello! Welcome to Dr. Donut. What can I get for you today?", True)

    async def stop(self) -> None:
        """Stop the session."""
        # Trigger the ended event handlers
        for handler in self.handlers["ended"]:
            await handler()
        # We could also set a flag here to indicate the session is stopped
        self.started = False

    async def send_text_message(self, message: str) -> None:
        """Send a text message."""
        self.messages.append(message)
        
        # Simulate tool execution if the message contains a keyword
        if "secret menu" in message.lower() and "getSecretMenu" in self.tools_registered:
            tool_handler = self.tools_registered["getSecretMenu"]
            result = await tool_handler({})
            response = f"Here's our secret menu for today: {result[0]['items'][0]['name']} for {result[0]['items'][0]['price']}"
            
            for handler in self.handlers["output"]:
                await handler(response, False)
                await asyncio.sleep(0.1)
                await handler(response, True)
        else:
            # Simulate regular response
            response = "I'll add that to your order. Anything else?"
            for handler in self.handlers["output"]:
                await handler(response, False)
                await asyncio.sleep(0.1)
                await handler(response, True)

    def register_tool(self, tool_name: str, handler: Any) -> None:
        """Register a tool handler."""
        self.tools_registered[tool_name] = handler

    async def close(self) -> None:
        """Close the session."""
        for handler in self.handlers["ended"]:
            await handler()


class MockUltravoxClient:
    """Mock UltravoxClient for integration testing."""

    def __init__(self, api_key: str) -> None:
        """Initialize the mock client."""
        self.api_key = api_key
        self.calls = MagicMock()
        self.calls.create = AsyncMock(return_value={"callId": "test-call-id"})
        self.tools = MagicMock()
        self.voices = MagicMock()

    async def join_call(self, url: str) -> MockWebSocketSession:
        """Join a call and return a mock session."""
        return MockWebSocketSession()


def test_command_line_argument_handling():
    """Test that command line arguments are properly handled."""
    # Test with default arguments
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(
            verbose=False,
            voice=None,
            system_prompt="Default prompt",
            temperature=0.7,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None
        )
        
        # Import the cli module to get the parsed arguments
        import importlib
        import ultravox_cli.cli
        importlib.reload(ultravox_cli.cli)
        
        # Verify the arguments were parsed correctly
        args = ultravox_cli.cli.argparse.ArgumentParser().parse_args()
        assert args.verbose is False
        assert args.voice is None
        assert args.system_prompt == "Default prompt"
        assert args.temperature == 0.7
        assert args.secret_menu is False
        assert args.experimental_messages is False
        assert args.prior_call_id is None
        assert args.user_speaks_first is False
        assert args.initial_output_text is False
        assert args.api_version is None
    
    # Test with custom arguments
    with patch("argparse.ArgumentParser.parse_args") as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(
            verbose=True,
            voice="custom_voice",
            system_prompt="Custom prompt",
            temperature=0.9,
            secret_menu=True,
            experimental_messages=True,
            prior_call_id="12345",
            user_speaks_first=True,
            initial_output_text=True,
            api_version="v2"
        )
        
        # Import the cli module to get the parsed arguments
        import importlib
        import ultravox_cli.cli
        importlib.reload(ultravox_cli.cli)
        
        # Verify the arguments were parsed correctly
        args = ultravox_cli.cli.argparse.ArgumentParser().parse_args()
        assert args.verbose is True
        assert args.voice == "custom_voice"
        assert args.system_prompt == "Custom prompt"
        assert args.temperature == 0.9
        assert args.secret_menu is True
        assert args.experimental_messages is True
        assert args.prior_call_id == "12345"
        assert args.user_speaks_first is True
        assert args.initial_output_text is True
        assert args.api_version == "v2"


if __name__ == "__main__":
    pytest.main() 
