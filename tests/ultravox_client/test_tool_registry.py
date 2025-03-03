import asyncio
import inspect
import logging
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any

from ultravox_cli.ultravox_client.tool_registry import ToolRegistry


class TestToolRegistry:
    """Tests for the ToolRegistry class."""

    def setup_method(self):
        """Set up a fresh ToolRegistry for each test."""
        self.registry = ToolRegistry()

    def test_init(self):
        """Test that registry is initialized properly."""
        assert hasattr(self.registry, "_tools")
        assert isinstance(self.registry._tools, dict)
        assert len(self.registry._tools) == 0

    def test_register_tool(self):
        """Test registering a tool."""

        # Define a sample tool
        def sample_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        # Register the tool
        self.registry.register(
            name="test_tool",
            handler=sample_handler,
            description="A test tool",
            parameters={"type": "object", "properties": {}},
        )

        # Verify the tool was registered
        assert "test_tool" in self.registry._tools
        tool_def = self.registry._tools["test_tool"]
        assert tool_def["name"] == "test_tool"
        assert tool_def["description"] == "A test tool"
        assert tool_def["handler"] == sample_handler
        assert "parameters" in tool_def

    def test_register_tool_with_minimal_params(self):
        """Test registering a tool with minimal parameters."""

        def sample_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        # Register with minimal parameters (no schema)
        self.registry.register(
            name="minimal_tool", handler=sample_handler, description="A minimal tool"
        )

        # Verify the tool was registered with default parameters
        assert "minimal_tool" in self.registry._tools
        tool_def = self.registry._tools["minimal_tool"]
        assert tool_def["parameters"] == {"type": "object", "properties": {}}

    def test_register_duplicate_tool(self):
        """Test that registering a duplicate tool raises an error."""

        def sample_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        # Register a tool
        self.registry.register(
            name="duplicate_tool",
            handler=sample_handler,
            description="First registration",
        )

        # Try to register another tool with the same name
        with pytest.raises(ValueError) as excinfo:
            self.registry.register(
                name="duplicate_tool",
                handler=sample_handler,
                description="Second registration",
            )

        assert "is already registered" in str(excinfo.value)

    def test_register_invalid_parameters(self):
        """Test that registering a tool with invalid parameters raises an error."""

        def sample_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        # Try to register with non-dict parameters
        with pytest.raises(ValueError) as excinfo:
            self.registry.register(
                name="invalid_params_tool",
                handler=sample_handler,
                description="Invalid params tool",
                parameters="not_a_dict",  # Invalid parameters
            )

        assert "Parameters must be a dictionary" in str(excinfo.value)

        # Try to register with parameters missing 'properties'
        with pytest.raises(ValueError) as excinfo:
            self.registry.register(
                name="missing_properties_tool",
                handler=sample_handler,
                description="Missing properties tool",
                parameters={"type": "object"},  # Missing 'properties'
            )

        assert "Parameters must have a 'properties' field" in str(excinfo.value)

    def test_unregister_tool(self):
        """Test unregistering a tool."""

        # First register a tool
        def sample_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        self.registry.register(
            name="tool_to_unregister",
            handler=sample_handler,
            description="Tool to unregister",
        )

        # Verify it was registered
        assert "tool_to_unregister" in self.registry._tools

        # Unregister the tool
        self.registry.unregister("tool_to_unregister")

        # Verify it was unregistered
        assert "tool_to_unregister" not in self.registry._tools

    def test_unregister_nonexistent_tool(self):
        """Test that unregistering a nonexistent tool raises an error."""
        with pytest.raises(ValueError) as excinfo:
            self.registry.unregister("nonexistent_tool")

        assert "is not registered" in str(excinfo.value)

    def test_get_tool(self):
        """Test getting a tool by name."""

        # First register a tool
        def sample_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success"}

        self.registry.register(
            name="tool_to_get", handler=sample_handler, description="Tool to get"
        )

        # Get the tool
        tool_def = self.registry.get_tool("tool_to_get")

        # Verify the returned tool definition
        assert tool_def["name"] == "tool_to_get"
        assert tool_def["description"] == "Tool to get"
        assert tool_def["handler"] == sample_handler

    def test_get_nonexistent_tool(self):
        """Test that getting a nonexistent tool raises an error."""
        with pytest.raises(ValueError) as excinfo:
            self.registry.get_tool("nonexistent_tool")

        assert "is not registered" in str(excinfo.value)

    def test_list_tools(self):
        """Test listing all registered tools."""

        # Register a few tools
        def handler1(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success1"}

        def handler2(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": "success2"}

        self.registry.register(name="tool1", handler=handler1, description="Tool 1")

        self.registry.register(name="tool2", handler=handler2, description="Tool 2")

        # List the tools
        tools_list = self.registry.list_tools()

        # Verify the list content
        assert len(tools_list) == 2

        # Check that handler is not included in the results
        for tool in tools_list:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert "handler" not in tool

    @pytest.mark.asyncio
    async def test_execute_tool_sync(self):
        """Test executing a synchronous tool."""

        # Register a synchronous tool
        def sync_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": f"Got {params.get('input', 'nothing')}"}

        self.registry.register(
            name="sync_tool", handler=sync_handler, description="Synchronous tool"
        )

        # Execute the tool
        result = await self.registry.execute_tool("sync_tool", {"input": "test_value"})

        # Verify the result
        assert result == {"result": "Got test_value"}

    @pytest.mark.asyncio
    async def test_execute_tool_async(self):
        """Test executing an asynchronous tool."""

        # Register an asynchronous tool
        async def async_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": f"Got {params.get('input', 'nothing')}"}

        self.registry.register(
            name="async_tool", handler=async_handler, description="Asynchronous tool"
        )

        # Execute the tool
        result = await self.registry.execute_tool("async_tool", {"input": "test_value"})

        # Verify the result
        assert result == {"result": "Got test_value"}

    @pytest.mark.asyncio
    async def test_execute_nonexistent_tool(self):
        """Test that executing a nonexistent tool raises an error."""
        with pytest.raises(ValueError) as excinfo:
            await self.registry.execute_tool("nonexistent_tool", {})

        assert "is not registered" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_execute_tool_error(self):
        """Test that errors in tool execution are properly handled."""

        # Register a tool that raises an exception
        def error_handler(params: Dict[str, Any]) -> Dict[str, Any]:
            raise ValueError("Test error")

        self.registry.register(
            name="error_tool",
            handler=error_handler,
            description="Tool that raises an error",
        )

        # Create a real logger to test
        logger = logging.getLogger("ultravox_cli.ultravox_client.tool_registry")

        # Setup mock logger
        with patch.object(logger, "error") as mock_error:
            # Execute the tool and verify the error is propagated
            with pytest.raises(ValueError) as excinfo:
                await self.registry.execute_tool("error_tool", {})

            assert "Test error" in str(excinfo.value)

            # Verify that the error was logged
            mock_error.assert_called_once()
            assert "error_tool" in mock_error.call_args[0][0]
