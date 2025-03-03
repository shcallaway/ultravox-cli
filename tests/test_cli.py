import os
import sys
import asyncio
import argparse
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from typing import Any, Dict, List, Optional, Tuple

from ultravox_cli.cli import (
    _add_query_param,
    create_call,
    get_secret_menu,
    create_output_handler,
    setup_session_handlers,
    run_conversation_loop,
    main,
)

from ultravox_cli.ultravox_client.client import UltravoxClient


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
    mock_client.calls.create = AsyncMock(return_value={"joinUrl": "https://example.com/test"})
    
    # Create mock args
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.secret_menu = False
    mock_args.api_version = None
    mock_args.experimental_messages = False
    
    # Call the function
    join_url = await create_call(mock_client, mock_args)
    
    # Verify the result
    assert join_url == "https://example.com/test"
    
    # Verify that client.calls.create was called once
    mock_client.calls.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_call_with_secret_menu():
    """Test the create_call function with secret menu enabled."""
    # Create mock client
    mock_client = MagicMock()
    mock_client.calls = MagicMock()
    mock_client.calls.create = AsyncMock(return_value={"joinUrl": "https://example.com/test"})
    
    # Create mock args
    mock_args = MagicMock()
    mock_args.system_prompt = "Test system prompt"
    mock_args.temperature = 0.8
    mock_args.voice = None
    mock_args.secret_menu = True
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
    
    # Verify that "secret menu" is in the system_prompt
    assert "system_prompt" in call_kwargs
    assert "secret menu" in call_kwargs["system_prompt"]
    
    # Verify that selected_tools was included in the kwargs
    assert "selected_tools" in call_kwargs
    assert any(
        tool.get("temporaryTool", {}).get("modelToolName") == "getSecretMenu"
        for tool in call_kwargs["selected_tools"]
    )


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
        agent_response_complete
    )
    
    # Test with a mock message
    with patch('builtins.print'):  # Suppress print statements
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
    agent_response_ref, agent_response_complete = await setup_session_handlers(session, done)
    
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
    
    mock_handlers = MagicMock()
    mock_args = MagicMock()
    done_event = asyncio.Event()
    
    # Mock agent_response_ref and agent_response_complete
    agent_response_ref = ["Initial response"]
    agent_response_complete = asyncio.Event()
    agent_response_complete.set()
    
    # Mock input to return "exit" after one loop
    with patch('builtins.input', return_value="exit"), \
         patch('builtins.print'):  # Suppress print statements
        
        # Create the task
        task = asyncio.create_task(
            run_conversation_loop(
                mock_session, 
                done_event, 
                agent_response_ref, 
                agent_response_complete
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
        api_version=None
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
    with patch("ultravox_cli.cli.UltravoxClient", return_value=mock_client), \
         patch("ultravox_cli.cli.create_call", mock_create_call), \
         patch("ultravox_cli.cli.setup_session_handlers", mock_setup_handlers), \
         patch("ultravox_cli.cli.run_conversation_loop", mock_run_loop), \
         patch.dict("os.environ", {"ULTRAVOX_API_KEY": "test_key"}):
        
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
