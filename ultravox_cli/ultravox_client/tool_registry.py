"""
Tool registry for managing client-side tools in Ultravox applications.

This module provides the ToolRegistry class, which manages the registration,
validation, and execution of client-side tools that can be invoked by the
Ultravox agent during a conversation.

Tools are defined with a name, handler function, description, and optional
parameter schema. When registered, tools can be executed by the agent during
a conversation to perform client-side operations.

Example:
    ```python
    from ultravox_cli.ultravox_client.tool_registry import ToolRegistry

    # Create a tool registry
    registry = ToolRegistry()

    # Define a tool handler
    async def get_weather(parameters):
        location = parameters.get("location", "New York")
        return {"temperature": 72, "condition": "sunny", "location": location}

    # Register the tool
    registry.register(
        name="getWeather",
        handler=get_weather,
        description="Get the current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get weather for"
                }
            }
        }
    )

    # Later, execute the tool
    async def example():
        result = await registry.execute_tool("getWeather", {"location": "San Francisco"})
        print(result)  # {"temperature": 72, "condition": "sunny", "location": "San Francisco"}
    ```
"""

import inspect
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for client-side tools that can be invoked by the Ultravox agent.

    This class provides methods for registering, validating, and executing tools.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        handler: Callable,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a tool with the registry.

        Args:
            name: The name of the tool
            handler: The function to handle tool invocations
            description: A description of what the tool does
            parameters: JSON Schema for the tool parameters

        Raises:
            ValueError: If the tool is already registered or parameters are invalid
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        # Validate parameters if provided
        if parameters:
            if not isinstance(parameters, dict):
                raise ValueError("Parameters must be a dictionary")

            # Ensure parameters have the required fields
            if "type" not in parameters:
                parameters["type"] = "object"

            if "properties" not in parameters:
                raise ValueError("Parameters must have a 'properties' field")

        # Create tool definition
        tool_def = {
            "name": name,
            "description": description,
            "parameters": parameters or {"type": "object", "properties": {}},
            "handler": handler,
        }

        self._tools[name] = tool_def
        logger.info(f"Registered tool: {name}")

    def unregister(self, name: str) -> None:
        """
        Unregister a tool from the registry.

        Args:
            name: The name of the tool to unregister

        Raises:
            ValueError: If the tool is not registered
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered")

        del self._tools[name]
        logger.info(f"Unregistered tool: {name}")

    def get_tool(self, name: str) -> Dict[str, Any]:
        """
        Get a tool definition by name.

        Args:
            name: The name of the tool

        Returns:
            The tool definition

        Raises:
            ValueError: If the tool is not registered
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered")

        return self._tools[name]

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all registered tools.

        Returns:
            A list of tool definitions (without handlers)
        """
        return [
            {k: v for k, v in tool.items() if k != "handler"}
            for tool in self._tools.values()
        ]

    async def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        """
        Execute a tool with the given parameters.

        Args:
            name: The name of the tool to execute
            parameters: The parameters to pass to the tool

        Returns:
            The result of the tool execution

        Raises:
            ValueError: If the tool is not registered
            Exception: If the tool execution fails
        """
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' is not registered")

        tool = self._tools[name]
        handler = tool["handler"]

        try:
            # Check if the handler is a coroutine function
            if inspect.iscoroutinefunction(handler):
                result = await handler(parameters)
            else:
                result = handler(parameters)

            return result
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}")
            raise
