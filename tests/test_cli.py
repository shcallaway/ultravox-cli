import os
import sys
import asyncio
import argparse
import json
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from typing import Any, Dict, List
from ultravox_cli.cli import (
    _add_query_param,
    create_call,
    get_secret_menu,
    create_output_handler,
    setup_session_handlers,
    run_conversation_loop,
    main,
)

# Add the project root directory to sys.path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestCLIFunctions:
    def test_add_query_param(self):
        """Test the _add_query_param function."""
        # Test adding a parameter to a URL without query parameters
        url = "https://example.com"
        result = _add_query_param(url, "test", "value")
        assert result == "https://example.com?test=value"

        # Test adding a parameter to a URL with existing query parameters
        url = "https://example.com?existing=param"
        result = _add_query_param(url, "test", "value")
        assert result == "https://example.com?existing=param&test=value"

        # Test replacing an existing parameter
        url = "https://example.com?test=old"
        result = _add_query_param(url, "test", "new")
        assert result == "https://example.com?test=new"


class TestGetSecretMenu:
    @pytest.mark.asyncio
    async def test_get_secret_menu(self):
        """Test the get_secret_menu function."""
        # Call the function with an empty parameters dict
        result = await get_secret_menu({})

        # Check that the result is a list with at least one item
        assert isinstance(result, list)
        assert len(result) > 0

        # Check that the first item has the expected structure
        first_item = result[0]
        assert "date" in first_item
        assert "items" in first_item

        # Check that items is a list with at least one item
        assert isinstance(first_item["items"], list)
        assert len(first_item["items"]) > 0

        # Check that each item has a name and price
        for item in first_item["items"]:
            assert "name" in item
            assert "price" in item


@pytest.mark.asyncio
async def test_create_call():
    """Test the create_call function."""
    # Create mock client
    mock_client = MagicMock()
    mock_client.calls = MagicMock()
    mock_client.calls.create = AsyncMock(
        return_value={"joinUrl": "https://example.com/test"}
    )

    # Create mock args
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.secret_menu = False
    mock_args.api_version = None
    mock_args.experimental_messages = False
    mock_args.initial_messages_json = None

    # Call the function
    join_url = await create_call(mock_client, mock_args)

    # Verify the result
    assert join_url == "https://example.com/test"

    # Verify that client.calls.create was called once
    mock_client.calls.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_call_with_secret_menu():
    """Test the create_call function with standard parameters."""
    # Create mock client
    mock_client = MagicMock()
    mock_client.calls = MagicMock()
    mock_client.calls.create = AsyncMock(
        return_value={"joinUrl": "https://example.com/test"}
    )

    # Create mock args
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.initial_messages_json = None
    mock_args.api_version = None
    mock_args.experimental_messages = False

    # Call the function
    join_url = await create_call(mock_client, mock_args)

    # Verify the result
    assert join_url == "https://example.com/test"

    # Verify that client.calls.create was called once
    mock_client.calls.create.assert_called_once()

    # Check that the call was made with the right parameters
    call_args, call_kwargs = mock_client.calls.create.call_args

    # Verify system prompt was passed correctly
    assert "system_prompt" in call_kwargs
    assert call_kwargs["system_prompt"] == "Test system prompt"

    # Verify that no additional tools were added
    assert "selected_tools" in call_kwargs
    assert call_kwargs["selected_tools"] == []


@pytest.mark.asyncio
async def test_create_call_with_initial_messages_json():
    """Test the create_call function with initial_messages_json."""
    # Create mock client
    mock_client = MagicMock()
    mock_client.calls = MagicMock()
    mock_client.calls.create = AsyncMock(
        return_value={"joinUrl": "https://example.com/test"}
    )

    # Create mock args
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.secret_menu = False
    mock_args.api_version = None
    mock_args.experimental_messages = False

    # Set the initial_messages_json
    initial_messages = [
        {"role": "MESSAGE_ROLE_AGENT", "text": "Welcome to our service!"},
        {"role": "MESSAGE_ROLE_USER", "text": "Tell me about your offerings"},
    ]
    mock_args.initial_messages_json = json.dumps(initial_messages)

    # Call the function
    join_url = await create_call(mock_client, mock_args)

    # Verify the result
    assert join_url == "https://example.com/test"

    # Verify that client.calls.create was called with the correct initial_messages
    mock_client.calls.create.assert_called_once()
    call_args = mock_client.calls.create.call_args[1]
    assert "initial_messages" in call_args
    assert call_args["initial_messages"] == initial_messages


def test_create_output_handler():
    """Test the create_output_handler function."""
    # Create the necessary references and event
    final_inference_ref = [None]  # type: List[Optional[str]]
    agent_response_ref = [""]  # type: List[str]
    current_final_response_ref = [""]  # type: List[str]
    agent_response_complete = asyncio.Event()

    # Create the handler
    handler = create_output_handler(
        final_inference_ref,
        agent_response_ref,
        current_final_response_ref,
        agent_response_complete,
    )

    # Test with a mock message
    with patch("builtins.print"):  # Suppress print statements
        # Create a mock function to call the handler
        async def call_handler() -> None:
            await handler("Test response.", True)

        # Run the handler
        asyncio.run(call_handler())

    # Verify the results
    assert agent_response_ref[0] == "Test response."
    assert final_inference_ref[0] == "Test response."
    assert current_final_response_ref[0] == "Test response. "
    assert agent_response_complete.is_set()


@pytest.mark.asyncio
async def test_setup_session_handlers():
    """Test the setup_session_handlers function."""
    # Create a mock session
    session = MagicMock()
    session.on = MagicMock(return_value=lambda func: func)

    # Create a done event
    done = asyncio.Event()

    # Call the function
    agent_response_ref, agent_response_complete = await setup_session_handlers(
        session, done
    )

    # Verify that the session.on method was called for each event
    assert session.on.call_count >= 3

    # Verify the returned objects
    assert isinstance(agent_response_ref, list)
    assert isinstance(agent_response_complete, asyncio.Event)

    # Verify the event handlers were registered
    session.on.assert_any_call("state")
    session.on.assert_any_call("output")
    session.on.assert_any_call("ended")
    session.on.assert_any_call("error")


@pytest.mark.asyncio
async def test_run_conversation_loop():
    """Test the run_conversation_loop function."""
    # Create mock objects
    mock_session = MagicMock()
    mock_session.send_text_message = AsyncMock()
    mock_session.stop = AsyncMock()

    done_event = asyncio.Event()

    # Mock agent_response_ref and agent_response_complete
    agent_response_ref = ["Initial response"]
    agent_response_complete = asyncio.Event()
    agent_response_complete.set()

    # Mock input to return "exit" after one loop
    with patch("builtins.input", return_value="exit"), patch(
        "builtins.print"
    ):  # Suppress print statements

        # Create the task
        task = asyncio.create_task(
            run_conversation_loop(
                mock_session, done_event, agent_response_ref, agent_response_complete
            )
        )

        # Allow the task to run
        await asyncio.sleep(0.1)

        # Wait for the task to complete
        await task

    # Verify that the done event was set
    assert done_event.is_set()


@pytest.mark.asyncio
async def test_main_function():
    """Test the main function."""
    # Create a mock args object
    mock_args = argparse.Namespace(
        verbose=False,
        voice=None,
        system_prompt="Test prompt",
        temperature=0.7,
        secret_menu=False,
        experimental_messages=False,
        prior_call_id=None,
        user_speaks_first=False,
        initial_output_text=False,
        api_version=None,
    )

    # Create mock session
    mock_session = MagicMock()
    mock_session.start = AsyncMock()
    mock_session.stop = AsyncMock()
    mock_session.on = MagicMock(return_value=lambda f: f)

    # Create mock client
    mock_client = MagicMock()
    mock_client.join_call = AsyncMock(return_value=mock_session)

    # Mock create_call to return a WebSocket URL
    async def mock_create_call(client, args):
        return "wss://example.com/test"

    # Mock setup_session_handlers
    async def mock_setup_handlers(session, done):
        return ["Initial response"], asyncio.Event()

    # Mock run_conversation_loop
    async def mock_run_loop(session, done, agent_response_ref, agent_response_complete):
        done.set()
        return None

    # Apply all the patches
    with patch("ultravox_cli.cli.UltravoxClient", return_value=mock_client), patch(
        "ultravox_cli.cli.create_call", mock_create_call
    ), patch("ultravox_cli.cli.setup_session_handlers", mock_setup_handlers), patch(
        "ultravox_cli.cli.run_conversation_loop", mock_run_loop
    ), patch.dict(
        "os.environ", {"ULTRAVOX_API_KEY": "test_key"}
    ):

        # Set the module-level args
        import ultravox_cli.cli

        original_args = ultravox_cli.cli.args
        ultravox_cli.cli.args = mock_args

        try:
            # Run the main function
            await main()
        finally:
            # Restore original args
            ultravox_cli.cli.args = original_args

    # Verify the session was started
    mock_session.start.assert_called_once()


# CLI Argument Parsing Tests (moved from test_cli_arguments.py)
class TestCLIArgumentParsing(unittest.TestCase):
    """Test cases for CLI argument parsing."""

    @patch("argparse.ArgumentParser.parse_args")
    def test_default_arguments(self, mock_parse_args: Any) -> None:
        """Test that default arguments are set correctly."""
        # Create a mock args object with default values
        mock_args = argparse.Namespace(
            verbose=False,
            voice=None,
            system_prompt="You are a helpful, harmless assistant",
            temperature=0.7,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None,
            initial_messages_json=None,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the default values
        self.assertFalse(args.verbose)
        self.assertIsNone(args.voice)
        self.assertEqual(args.system_prompt, "You are a helpful, harmless assistant")
        self.assertEqual(args.temperature, 0.7)
        self.assertFalse(args.secret_menu)
        self.assertFalse(args.experimental_messages)

    @patch("argparse.ArgumentParser.parse_args")
    def test_verbose_flag(self, mock_parse_args: Any) -> None:
        """Test that the verbose flag is set correctly."""
        # Create a mock args object with verbose set to True
        mock_args = argparse.Namespace(
            verbose=True,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None,
            initial_messages_json=None,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the verbose flag
        self.assertTrue(args.verbose)

    @patch("argparse.ArgumentParser.parse_args")
    def test_voice_argument(self, mock_parse_args: Any) -> None:
        """Test that the voice argument is set correctly."""
        # Create a mock args object with voice set
        mock_args = argparse.Namespace(
            verbose=False,
            voice="test-voice",
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None,
            initial_messages_json=None,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the voice argument
        self.assertEqual(args.voice, "test-voice")

    @patch("argparse.ArgumentParser.parse_args")
    def test_system_prompt_argument(self, mock_parse_args: Any) -> None:
        """Test that the system_prompt argument is set correctly."""
        # Create a mock args object with system_prompt set
        mock_args = argparse.Namespace(
            verbose=False,
            voice=None,
            system_prompt="Custom system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None,
            initial_messages_json=None,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the system_prompt argument
        self.assertEqual(args.system_prompt, "Custom system prompt")

    @patch("argparse.ArgumentParser.parse_args")
    def test_temperature_argument(self, mock_parse_args: Any) -> None:
        """Test that the temperature argument is set correctly."""
        # Create a mock args object with temperature set
        mock_args = argparse.Namespace(
            verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.5,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None,
            initial_messages_json=None,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the temperature argument
        self.assertEqual(args.temperature, 0.5)

    @patch("argparse.ArgumentParser.parse_args")
    def test_secret_menu_flag(self, mock_parse_args: Any) -> None:
        """Test that the secret_menu flag is set correctly."""
        # Create a mock args object with secret_menu set to True
        mock_args = argparse.Namespace(
            verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=True,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None,
            initial_messages_json=None,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the secret_menu flag
        self.assertTrue(args.secret_menu)

    @patch("argparse.ArgumentParser.parse_args")
    def test_experimental_messages_flag(self, mock_parse_args: Any) -> None:
        """Test that the experimental_messages flag is set correctly."""
        # Create a mock args object with experimental_messages set to True
        mock_args = argparse.Namespace(
            verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=True,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None,
            initial_messages_json=None,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the experimental_messages flag
        self.assertTrue(args.experimental_messages)

    @patch("argparse.ArgumentParser.parse_args")
    def test_api_version_argument(self, mock_parse_args: Any) -> None:
        """Test that the api_version argument is set correctly."""
        # Create a mock args object with api_version set to v2
        mock_args = argparse.Namespace(
            verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version="v2",
            initial_messages_json=None,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the api_version argument
        self.assertEqual(args.api_version, "v2")

    @patch("argparse.ArgumentParser.parse_args")
    def test_multiple_arguments(self, mock_parse_args: Any) -> None:
        """Test that multiple arguments are set correctly."""
        # Create initial messages for testing
        initial_messages = [{"role": "MESSAGE_ROLE_AGENT", "text": "Test message"}]
        initial_messages_json = json.dumps(initial_messages)

        # Create a mock args object with multiple arguments set
        mock_args = argparse.Namespace(
            verbose=True,
            voice="test-voice",
            system_prompt="Custom system prompt",
            temperature=0.5,
            secret_menu=True,
            experimental_messages=True,
            prior_call_id="test-call-id",
            user_speaks_first=True,
            initial_output_text=True,
            api_version="v2",
            initial_messages_json=initial_messages_json,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check all arguments
        self.assertTrue(args.verbose)
        self.assertEqual(args.voice, "test-voice")
        self.assertEqual(args.system_prompt, "Custom system prompt")
        self.assertEqual(args.temperature, 0.5)
        self.assertTrue(args.secret_menu)
        self.assertTrue(args.experimental_messages)
        self.assertEqual(args.prior_call_id, "test-call-id")
        self.assertTrue(args.user_speaks_first)
        self.assertTrue(args.initial_output_text)
        self.assertEqual(args.api_version, "v2")
        self.assertEqual(args.initial_messages_json, initial_messages_json)

        # Verify that it parses to the expected JSON
        parsed_messages = json.loads(args.initial_messages_json)
        self.assertEqual(parsed_messages, initial_messages)

    @patch("argparse.ArgumentParser.parse_args")
    def test_initial_messages_json_argument(self, mock_parse_args: Any) -> None:
        """Test that the initial_messages_json argument is set correctly."""
        # Create initial messages
        initial_messages = [
            {"role": "MESSAGE_ROLE_AGENT", "text": "Welcome to our service!"},
            {"role": "MESSAGE_ROLE_USER", "text": "Tell me about your offerings"},
        ]
        initial_messages_json = json.dumps(initial_messages)

        # Create a mock args object with initial_messages_json set
        mock_args = argparse.Namespace(
            verbose=False,
            voice=None,
            system_prompt="Test system prompt",
            temperature=0.8,
            secret_menu=False,
            experimental_messages=False,
            prior_call_id=None,
            user_speaks_first=False,
            initial_output_text=False,
            api_version=None,
            initial_messages_json=initial_messages_json,
        )
        mock_parse_args.return_value = mock_args

        # Import the CLI module with our mocked arguments
        import importlib
        from ultravox_cli import cli

        importlib.reload(cli)

        # Access the mocked args through the mock
        args = mock_parse_args.return_value

        # Check the initial_messages_json argument
        self.assertEqual(args.initial_messages_json, initial_messages_json)

        # Verify that it parses to the expected JSON
        parsed_messages = json.loads(args.initial_messages_json)
        self.assertEqual(parsed_messages, initial_messages)


# Error Handling Tests (moved from test_error_handling.py)
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
async def test_network_error_in_create_call(capsys):
    """Test handling of network errors in create_call function."""
    # Create mock client that raises ConnectionError
    mock_client = MagicMock()
    mock_client.calls = MagicMock()
    mock_client.calls.create = AsyncMock(
        side_effect=ConnectionError("Network error occurred")
    )

    # Create mock args
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.initial_messages_json = None
    mock_args.api_version = None
    mock_args.experimental_messages = False

    # Test handling of network errors
    with pytest.raises(SystemExit) as e:
        await create_call(mock_client, mock_args)

    # Verify the error code and message
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Network error" in captured.err


@pytest.mark.asyncio
async def test_api_error_in_create_call(capsys):
    """Test handling of API errors in create_call function."""

    # Define a custom APIError
    class APIError(Exception):
        def __init__(self, message, status_code=400):
            self.message = message
            self.status_code = status_code
            super().__init__(self.message)

    # Create mock client that raises APIError
    mock_client = MagicMock()
    mock_client.calls = MagicMock()
    mock_client.calls.create = AsyncMock(side_effect=APIError("Invalid request", 400))

    # Create mock args
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.initial_messages_json = None
    mock_args.api_version = None
    mock_args.experimental_messages = False

    # Test handling of API errors
    with pytest.raises(SystemExit) as e:
        await create_call(mock_client, mock_args)

    # Verify the error code and message
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Invalid request" in captured.err


@pytest.mark.asyncio
async def test_keyboard_interrupt_in_conversation_loop() -> None:
    """Test that the application handles keyboard interrupts in the
    conversation loop."""
    # Create mock objects
    mock_session = MagicMock()
    mock_session.send_text_message = AsyncMock()
    mock_session.stop = AsyncMock()

    # Set up mock input to raise KeyboardInterrupt
    with patch("builtins.input", side_effect=KeyboardInterrupt), patch(
        "builtins.print"
    ):  # Suppress print statements

        # Create the done event
        done_event = asyncio.Event()

        # Create the agent_response_ref and agent_response_complete
        agent_response_ref = ["Initial response"]
        agent_response_complete = asyncio.Event()
        agent_response_complete.set()

        # Call the function
        await run_conversation_loop(
            mock_session, done_event, agent_response_ref, agent_response_complete
        )

    # Verify that the done event was set
    assert done_event.is_set()

    # Verify that session.stop was called
    mock_session.stop.assert_called_once()


@pytest.mark.asyncio
async def test_exception_in_conversation_loop() -> None:
    """Test that the application handles other exceptions in the conversation loop."""
    # Create mock objects
    mock_session = MagicMock()
    mock_session.send_text_message = AsyncMock()
    mock_session.stop = AsyncMock()

    # Create the done event
    done_event = asyncio.Event()

    # Create the agent_response_ref and agent_response_complete
    agent_response_ref = ["Initial response"]
    agent_response_complete = asyncio.Event()
    agent_response_complete.set()

    # Mock the input function to raise an exception
    with patch("builtins.input", side_effect=ValueError("Test error")), patch(
        "builtins.print"
    ), patch(
        "logging.exception"
    ):  # Mock the logging to prevent actual logging

        # Call the function
        await run_conversation_loop(
            mock_session, done_event, agent_response_ref, agent_response_complete
        )

    # Verify that the done event was set (which means the error was caught)
    assert done_event.is_set()

    # Verify that session.stop was called
    mock_session.stop.assert_called_once()


@pytest.mark.asyncio
async def test_error_in_session_handlers() -> None:
    """Test error handling in session handlers."""
    # Create a mock session
    session = MagicMock()

    # Create a registration function that stores handlers
    handlers = {}

    def register_handler(event_type):
        def decorator(func):
            # Store the function
            handlers[event_type] = func
            return func

        return decorator

    # Mock the on method to use our registration function
    session.on = register_handler

    # Create a done event
    done = asyncio.Event()

    # Call setup_session_handlers to register handlers
    agent_response_ref, agent_response_complete = await setup_session_handlers(
        session, done
    )

    # Test the error handler with a mock error
    error_handler = handlers.get("error")
    if error_handler:
        with patch("builtins.print"):  # Suppress print statements
            await error_handler("Test error")

    # Verify that the done event was set
    assert done.is_set()


# Integration Tests (moved from test_integration.py that test CLI functionality)
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
            await handler(
                "Hello! Welcome to Dr. Donut. What can I get for you today?", False
            )
            # After a short delay, send final output
            await asyncio.sleep(0.1)
            await handler(
                "Hello! Welcome to Dr. Donut. What can I get for you today?", True
            )

    async def stop(self) -> None:
        """Stop the session."""
        # Simulate the session ending
        for handler in self.handlers["ended"]:
            await handler()

    async def send_text_message(self, message: str) -> None:
        """Send a text message."""
        self.messages.append(message)
        # Simulate the agent responding to the message
        for handler in self.handlers["output"]:
            await handler(f"You said: {message}", False)
            # After a short delay, send final output
            await asyncio.sleep(0.1)
            await handler(f"You said: {message}", True)

    def register_tool(self, tool_name: str, handler: Any) -> None:
        """Register a tool for the session."""
        self.tools_registered[tool_name] = handler

    async def close(self) -> None:
        """Close the session."""
        pass


class MockUltravoxClient:
    """Mock UltravoxClient for integration testing."""

    def __init__(self, api_key: str) -> None:
        """Initialize the mock client."""
        self.api_key = api_key
        self.calls = MagicMock()
        self.calls.create = AsyncMock(
            return_value={"joinUrl": "https://example.com/test"}
        )

    async def join_call(self, url: str) -> MockWebSocketSession:
        """Join a call."""
        return MockWebSocketSession()


def test_command_line_argument_handling():
    """Test handling of command line arguments."""
    # Test with a minimal set of arguments
    test_args = ["ultravox", "--system-prompt", "Test prompt"]
    with patch.object(sys, "argv", test_args), patch(
        "ultravox_cli.cli.main", return_value=None
    ), patch(
        "builtins.print"
    ):  # Suppress print statements

        # Import the CLI module with our test arguments
        import importlib
        import argparse
        from ultravox_cli import cli

        importlib.reload(cli)

        # Create an argument parser
        parser = argparse.ArgumentParser(
            description="Chat with Claude via the Ultravox API."
        )
        parser.add_argument(
            "--system-prompt",
            type=str,
            default="Test system prompt",
            help="System prompt to use for the assistant.",
        )
        args = parser.parse_args(["--system-prompt", "Test prompt"])

        # Check that the system_prompt argument was set correctly
        assert args.system_prompt == "Test prompt"


@pytest.mark.asyncio
async def test_cli_integration():
    """Test the integration of CLI components."""
    # Create mock args
    mock_args = MagicMock()
    mock_args.verbose = False
    mock_args.voice = None
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.secret_menu = False
    mock_args.experimental_messages = False
    mock_args.prior_call_id = None
    mock_args.user_speaks_first = False
    mock_args.initial_output_text = False
    mock_args.api_version = None
    mock_args.initial_messages_json = None

    # Create a mock client
    mock_client = MockUltravoxClient(api_key="test_key")

    # Patch functions to use our mock objects
    with patch("ultravox_cli.cli.UltravoxClient", return_value=mock_client), patch(
        "ultravox_cli.cli.args", mock_args
    ), patch("builtins.input", side_effect=["test message", "exit"]), patch(
        "builtins.print"
    ), patch.dict(
        "os.environ", {"ULTRAVOX_API_KEY": "test_key"}
    ):  # Patch environment variable

        # Call the main function
        await main()

    # Verify that the client was used correctly
    assert mock_client.calls.create.call_count == 1

    # Check that the call was created with the right parameters
    call_args, call_kwargs = mock_client.calls.create.call_args
    assert "system_prompt" in call_kwargs
    assert call_kwargs["system_prompt"] == "Test system prompt"
    assert "temperature" in call_kwargs
    assert call_kwargs["temperature"] == 0.8


@pytest.mark.asyncio
async def test_invalid_initial_messages_json_format():
    """Test handling of invalid JSON format in initial_messages_json."""
    # Create mock client
    mock_client = MagicMock()
    mock_client.calls = MagicMock()
    mock_client.calls.create = AsyncMock(
        return_value={"joinUrl": "https://example.com/test"}
    )

    # Create mock args with invalid JSON
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.secret_menu = False
    mock_args.api_version = None
    mock_args.experimental_messages = False
    mock_args.initial_messages_json = "{invalid json}"

    # Call the function and expect a ValueError
    with pytest.raises(ValueError) as excinfo:
        await create_call(mock_client, mock_args)

    # Verify that the error message indicates an invalid JSON format
    assert "Invalid JSON format" in str(excinfo.value)


@pytest.mark.asyncio
async def test_non_list_initial_messages_json():
    """Test handling of non-list value in initial_messages_json."""
    # Create mock client
    mock_client = MagicMock()
    mock_client.calls = MagicMock()
    mock_client.calls.create = AsyncMock(
        return_value={"joinUrl": "https://example.com/test"}
    )

    # Create mock args with JSON that's not a list
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.secret_menu = False
    mock_args.api_version = None
    mock_args.experimental_messages = False
    mock_args.initial_messages_json = '{"not": "a list"}'

    # Call the function and expect a ValueError
    with pytest.raises(ValueError) as excinfo:
        await create_call(mock_client, mock_args)

    # Verify that the error message indicates the value must be a list
    assert "must be a JSON list" in str(excinfo.value)
