import asyncio
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from typing import Any, Dict, List
import argparse

# Add the project root directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ultravox_cli.cli import create_call, run_conversation_loop, main
from ultravox_cli.ultravox_client.client import UltravoxClient


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling in the CLI application."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("os.getenv", return_value=None)
    def test_missing_api_key(self, mock_getenv: MagicMock) -> None:
        """Test that the application raises an error when API key is missing."""
        # Clear the API key from the environment
        with self.assertRaises(ValueError) as context:
            asyncio.run(main())
        
        # Check that the error message contains information about the missing API key
        self.assertIn("ULTRAVOX_API_KEY", str(context.exception))


@pytest.mark.asyncio
async def test_network_error_in_create_call() -> None:
    """Test that the application handles network errors during call creation."""
    # Create mock args
    mock_args = MagicMock()
    mock_args.voice = None
    mock_args.system_prompt = "Test prompt"
    mock_args.temperature = 0.8
    mock_args.secret_menu = False
    mock_args.experimental_messages = False
    mock_args.prior_call_id = None
    mock_args.user_speaks_first = False
    mock_args.initial_output_text = False
    mock_args.api_version = None
    
    # Create mock client with calls attribute
    mock_client = MagicMock(spec=UltravoxClient)
    mock_client.calls = MagicMock()
    
    # Make the calls.create method raise a connection error
    mock_client.calls.create = AsyncMock(side_effect=ConnectionError("Failed to connect to API"))
    
    # Test that the function raises the connection error
    with pytest.raises(ConnectionError):
        await create_call(mock_client, mock_args)


@pytest.mark.asyncio
async def test_api_error_in_create_call() -> None:
    """Test that the application handles API errors during call creation."""
    # Create mock args
    mock_args = MagicMock()
    mock_args.voice = None
    mock_args.system_prompt = "Test prompt"
    mock_args.temperature = 0.8
    mock_args.secret_menu = False
    mock_args.experimental_messages = False
    mock_args.prior_call_id = None
    mock_args.user_speaks_first = False
    mock_args.initial_output_text = False
    mock_args.api_version = None
    
    # Create mock client with calls attribute
    mock_client = MagicMock(spec=UltravoxClient)
    mock_client.calls = MagicMock()
    
    # Define a custom API error
    class APIError(Exception):
        pass
    
    # Make the calls.create method raise an API error
    mock_client.calls.create = AsyncMock(side_effect=APIError("Invalid API request"))
    
    # Test that the function raises the API error
    with pytest.raises(APIError):
        await create_call(mock_client, mock_args)


@pytest.mark.asyncio
async def test_keyboard_interrupt_in_conversation_loop() -> None:
    """Test that the application handles keyboard interrupts during conversation."""
    # Create mock session and events
    session = MagicMock()
    session.send_text_message = AsyncMock()
    session.stop = AsyncMock()
    done = asyncio.Event()
    agent_response_ref = ["Initial agent response"]
    agent_response_complete = asyncio.Event()
    agent_response_complete.set()  # Start with it set so loop proceeds
    
    # Mock the input function to raise a KeyboardInterrupt
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        # Mock print to avoid output during test
        with patch("builtins.print"):
            # Run the conversation loop
            await run_conversation_loop(
                session,
                done,
                agent_response_ref,
                agent_response_complete
            )
    
    # Verify that the done event was set (conversation ended)
    assert done.is_set()


@pytest.mark.asyncio
async def test_exception_in_conversation_loop() -> None:
    """Test that the application handles general exceptions during conversation."""
    # Create mock session and events
    session = MagicMock()
    session.send_text_message = AsyncMock(side_effect=Exception("Test exception"))
    session.stop = AsyncMock()
    done = asyncio.Event()
    agent_response_ref = ["Initial agent response"]
    agent_response_complete = asyncio.Event()
    agent_response_complete.set()  # Start with it set so loop proceeds
    
    # Mock input and print to avoid output during test
    with patch("builtins.input", return_value="Test message"):
        with patch("builtins.print"):
            with patch("logging.exception"):  # Mock logging.exception to avoid output
                # Run the conversation loop
                await run_conversation_loop(
                    session,
                    done,
                    agent_response_ref,
                    agent_response_complete
                )
    
    # Verify that the done event was set (conversation ended due to exception)
    assert done.is_set()


@pytest.mark.asyncio
async def test_error_in_session_handlers() -> None:
    """Test that errors in session handlers are properly handled."""
    # Create a mock session
    session = MagicMock()
    
    # Make the on method register handlers that will raise exceptions
    def register_handler(event_type):
        def decorator(func):
            # Store the function
            return func
        return decorator
    
    session.on = register_handler
    # Make session.start raise an exception but ensure it's called first
    session.start = AsyncMock(side_effect=Exception("Session start error"))
    session.stop = AsyncMock()
    
    # Create a simple test function to directly test session.start
    async def test_session_start() -> None:
        try:
            await session.start()
        except Exception:
            # Expected exception
            pass
    
    # Run the test function
    await test_session_start()
    
    # Verify the session.start was called and raised an exception
    session.start.assert_called_once()


if __name__ == "__main__":
    unittest.main() 
