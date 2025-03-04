"""
WebSocket-based session management for Ultravox voice calls.

This module provides the WebsocketSession class, which handles real-time
communication with the Ultravox service via WebSockets. It manages the connection
lifecycle, processes incoming events, and handles client-side tool invocations.

The session is event-driven and emits various events that clients can listen for:
- 'state': When the call state changes (idle, listening, thinking, speaking)
- 'output': When the agent produces output
- 'error': When an error occurs
- 'ended': When the session ends

Example:
    ```python
    from ultravox_cli.ultravox_client.websocket_session import WebsocketSession

    # Create a session from a join URL
    session = WebsocketSession("wss://api.ultravox.ai/api/calls/join/...")

    # Register event handlers
    @session.on("state")
    async def on_state(state):
        print(f"State changed: {state}")

    @session.on("output")
    async def on_output(text, final):
        print(f"Agent: {text}")

    # Register a tool
    session.register_tool("getWeather", get_weather_handler)

    # Start the session
    await session.start()

    # Send a message
    await session.send_text_message("Hello!")

    # Stop the session when done
    await session.stop()
    ```
"""

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Literal, Optional, Union

import pyee.asyncio
from websockets import exceptions as ws_exceptions
from websockets.asyncio import client as ws_client


class WebsocketSession(pyee.asyncio.AsyncIOEventEmitter):
    """
    A websocket-based voice session that connects to an Ultravox call.

    The session continuously streams audio in and out and emits events for state changes
    and agent messages. It also handles client tool invocations.

    Events:
        - state: Emitted when the call state changes (idle, listening, thinking,
          speaking)
        - output: Emitted when the agent produces output (text, final)
        - error: Emitted when an error occurs
        - ended: Emitted when the session ends
    """

    def __init__(self, join_url: str):
        """
        Initialize a WebSocket session.

        Args:
            join_url: The join URL for the call
        """
        super().__init__()
        self._state: Literal["idle", "listening", "thinking", "speaking"] = "idle"
        self._pending_output = ""
        self._url = join_url
        self._socket: Optional[ws_client.ClientConnection] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._tool_handlers: Dict[str, Callable] = {}

    async def start(self) -> None:
        """
        Start the session by connecting to the WebSocket.
        """
        logging.debug(f"Connecting to {self._url}")
        self._socket = await ws_client.connect(self._url)
        self._receive_task = asyncio.create_task(self._socket_receive(self._socket))

    async def stop(self) -> None:
        """
        End the session, closing the connection and ending the call.
        """
        logging.debug("Stopping WebSocket session...")
        await self._async_close(
            self._socket.close() if self._socket else None,
            self._async_cancel(self._receive_task),
        )
        if self._state != "idle":
            self._state = "idle"
            self.emit("state", "idle")

    async def _socket_receive(self, socket: ws_client.ClientConnection) -> None:
        """
        Receive and process messages from the WebSocket.

        Args:
            socket: The WebSocket connection
        """
        try:
            async for message in socket:
                await self._on_socket_message(message)
        except asyncio.CancelledError:
            logging.debug("Socket receive task cancelled")
        except ws_exceptions.ConnectionClosedOK:
            logging.debug("Socket closed normally")
        except ws_exceptions.ConnectionClosedError as e:
            self.emit("error", e)
            return
        logging.debug("Socket receive task completed")
        self.emit("ended")

    async def _on_socket_message(self, payload: Union[str, bytes]) -> None:
        """
        Process a message received from the WebSocket.

        Args:
            payload: The message payload (string or bytes)
        """
        if isinstance(payload, bytes):
            # Handle audio data if needed
            return
        elif isinstance(payload, str):
            msg = json.loads(payload)
            await self._handle_data_message(msg)

    async def _handle_data_message(self, msg: Dict[str, Any]) -> None:
        """
        Handle a data message from the WebSocket.

        Args:
            msg: The message data
        """
        msg_type = msg.get("type")

        if msg_type == "playback_clear_buffer":
            # Handle buffer clearing if needed
            pass
        elif msg_type == "state":
            if msg["state"] != self._state:
                self._state = msg["state"]
                self.emit("state", msg["state"])
        elif msg_type == "transcript":
            # Handle transcript messages
            if msg.get("role") != "agent":
                return  # Ignore user transcripts

            if msg.get("text") is not None:
                self._pending_output = msg["text"]
                self.emit("output", msg["text"], msg["final"])
            else:
                self._pending_output += msg.get("delta", "")
                self.emit("output", self._pending_output, msg["final"])

            if msg.get("final", False):
                self._pending_output = ""
        elif msg_type == "client_tool_invocation":
            await self._handle_client_tool_call(
                msg["toolName"], msg["invocationId"], msg.get("parameters", {})
            )
        elif msg_type == "debug":
            logging.debug(f"Debug message: {msg.get('message')}")
        else:
            logging.warning(f"Unhandled message type: {msg_type}")

    async def _handle_client_tool_call(
        self, tool_name: str, invocation_id: str, parameters: Dict[str, Any]
    ) -> None:
        """
        Handle a client tool invocation.

        This method is called when the agent invokes a client-side tool. It looks up the
        registered handler for the specified tool, calls it with the provided parameters,
        and sends the result back to the server.

        Args:
            tool_name: The name of the tool to invoke
            invocation_id: The unique ID for this tool invocation, used to match the response
            parameters: The parameters to pass to the tool handler

        Note:
            If no handler is registered for the tool, an error response is sent.
            If the handler raises an exception, the error information is captured and sent.

        Example of a tool invocation response:
            {
                "type": "client_tool_result",
                "invocationId": "123",
                "result": "{\"data\": \"example result\"}"
            }

            or in case of error:

            {
                "type": "client_tool_result",
                "invocationId": "123",
                "errorType": "ValueError",
                "errorMessage": "Invalid parameter"
            }
        """
        logging.debug(f"Client tool call: {tool_name}")

        response: Dict[str, Any] = {
            "type": "client_tool_result",
            "invocationId": invocation_id,
        }

        # Check if we have a registered handler for this tool
        if tool_name in self._tool_handlers:
            try:
                result = await self._tool_handlers[tool_name](parameters)
                response["result"] = json.dumps(result)
            except Exception as e:
                response["errorType"] = type(e).__name__
                response["errorMessage"] = str(e)
        else:
            response["errorType"] = "undefined"
            response["errorMessage"] = f"Unknown tool: {tool_name}"

        if self._socket:
            await self._socket.send(json.dumps(response))

    def register_tool(self, tool_name: str, handler: Callable) -> None:
        """
        Register a handler for a client tool.

        Args:
            tool_name: The name of the tool
            handler: The function to handle tool invocations
        """
        self._tool_handlers[tool_name] = handler

    async def _async_close(self, *awaitables_or_none: Optional[Awaitable]) -> None:
        """
        Close multiple awaitables, handling exceptions.

        This utility method safely awaits multiple coroutines, catching and handling
        any exceptions that may occur. It's used for graceful shutdown of multiple
        tasks or connections.

        Args:
            *awaitables_or_none: Awaitable objects to close. Can include None values,
                                which will be ignored.

        Note:
            This method uses asyncio.shield to prevent cancellation of the gather
            operation itself. If multiple exceptions occur, they are combined into
            a single error message rather than using ExceptionGroup.

        Implementation Details:
            - None values are filtered out
            - Cancelled exceptions are ignored
            - Other exceptions are logged with a warning
        """
        coros = [coro for coro in awaitables_or_none if coro is not None]
        if not coros:
            return

        maybe_exceptions = await asyncio.shield(
            asyncio.gather(*coros, return_exceptions=True)
        )

        non_cancelled_exceptions = [
            exc
            for exc in maybe_exceptions
            if isinstance(exc, Exception)
            and not isinstance(exc, asyncio.CancelledError)
        ]

        if non_cancelled_exceptions:
            if len(non_cancelled_exceptions) == 1:
                to_report = non_cancelled_exceptions[0]
            else:
                # Create a message with all exceptions instead of using ExceptionGroup
                error_msg = (
                    f"Multiple failures: "
                    f"{', '.join(str(e) for e in non_cancelled_exceptions)}"
                )
                to_report = RuntimeError(error_msg)

            logging.warning("Error during async close", exc_debug=to_report)

    async def _async_cancel(self, *tasks_or_none: Optional[asyncio.Task]) -> None:
        """
        Cancel multiple tasks, handling exceptions.

        This utility method safely cancels multiple asyncio tasks and waits for them
        to complete or raise exceptions. It's used during cleanup to ensure all
        background tasks are properly terminated.

        Args:
            *tasks_or_none: Task objects to cancel. Can include None values,
                           which will be ignored.

        Note:
            This method first cancels all provided tasks, then uses _async_close to
            wait for them to complete or raise exceptions. Any resulting exceptions
            are handled by _async_close.
        """
        tasks = [task for task in tasks_or_none if task is not None]
        for task in tasks:
            task.cancel()

        await self._async_close(*tasks)

    async def send_text_message(self, text: str) -> None:
        """
        Send a text message from the user to the agent.

        This method follows the inputTextMessage schema from the UltraVox documentation
        to send a user's text input to the agent during an ongoing conversation.

        Args:
            text: The user's text message
        """
        if not self._socket:
            raise RuntimeError("Socket not connected. Call start() first.")

        message = {"type": "input_text_message", "text": text}

        logging.debug(f"Sending user message: {text}")
        await self._socket.send(json.dumps(message))
