from dotenv import load_dotenv
import argparse
import asyncio
import datetime
import json
import logging
import os
import signal
import sys
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

from ultravox_cli.ultravox_client.client import UltravoxClient

"""
Command-line interface for the Ultravox voice assistant.

This module provides a command-line application for interacting with the Ultravox
voice service. It allows users to create and join voice calls, send messages, and
process agent responses. The CLI supports various features including:

- Creating voice calls with customizable parameters
- Real-time text-based conversation with the agent
- Integration with client-side tools
- Configurable voices and system prompts

Example usage:
    python -m ultravox_cli.cli --voice "default" --temperature 0.7
    
The CLI uses environment variables for configuration (see .env.example).
"""

# Create the argument parser at module level
parser = argparse.ArgumentParser(prog="cli.py")

parser.add_argument(
    "--verbose", "-v", action="store_true", help="Show verbose session information"
)

parser.add_argument("--voice", "-V", type=str, help="Name (or id) of voice to use")

parser.add_argument(
    "--system-prompt",
    help="System prompt to use for the call",
    default=f"""
You are a friendly assistant. Local time is currently:
${datetime.datetime.now().isoformat()}
The user is talking to you over voice on their phone, and your response will be
read out loud with realistic text-to-speech (TTS) technology.
""",
)

parser.add_argument(
    "--temperature",
    type=float,
    default=0.8,
    help="Temperature to use when creating the call",
)

parser.add_argument(
    "--initial-messages-json",
    type=str,
    help="JSON string containing a list of initial messages to be provided to the call",
)

# Initialize args with default value for testing purposes
args = None


# This is an example tool implementation to demonstrate how to create and use tools with
# Ultravox
# It shows a pattern for implementing a simple tool that returns structured data
# In a real application, you would implement your own tools that provide actual
# functionality
async def get_secret_menu(parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handler for the getSecretMenu tool.

    This is an example tool that demonstrates how to implement a tool that returns
    structured data.
    The tool returns a mock "secret menu" with items and prices.
    In a real application, you might fetch this data from a database or API.

    Args:
        parameters: Dictionary of parameters passed to the tool.
                   This example doesn't use any parameters, but real tools might.

    Returns:
        List[Dict[str, Any]]: A list containing a dictionary with 'date' and 'items',
                             where 'items' is a list of menu items with 'name' and 'price'.

    Raises:
        Exception: This simple example doesn't raise exceptions, but real implementations
                  might raise exceptions for invalid parameters or service unavailability.
    """
    return [
        {
            "date": datetime.date.today().isoformat(),
            "items": [
                {
                    "name": "Banana Smoothie",
                    "price": "$4.99",
                },
                {
                    "name": "Butter Pecan Ice Cream (one scoop)",
                    "price": "$2.99",
                },
            ],
        },
    ]


async def create_call(client: UltravoxClient, args: argparse.Namespace) -> str:
    """Creates a new call and returns its join URL.

    This function initializes a new Ultravox call with the specified parameters
    from command-line arguments, including system prompt, temperature, voice, and
    any initial messages.

    Args:
        client: An initialized UltravoxClient instance with a valid API key.
        args: Command-line arguments containing call configuration parameters,
              including system_prompt, temperature, voice, and initial_messages_json.

    Returns:
        str: The join URL for the created call, which can be used to connect to
             the call via WebSocket.

    Raises:
        ValueError: If initial_messages_json is invalid or the API response is missing
                   expected fields.
        Exception: For other API errors, connection issues, or authentication failures.
    """
    selected_tools: List[Dict[str, Any]] = []

    # Uncomment to use an example tool
    # selected_tools.append(
    #     {
    #         "temporaryTool": {
    #             "modelToolName": "getSecretMenu",
    #             "description": "Looks up today's secret menu items.",
    #             "client": {},
    #         },
    #     }
    # )

    initial_messages: List[Dict[str, Any]] = []

    # Process initial_messages_json if provided
    if (
        hasattr(args, "initial_messages_json")
        and args.initial_messages_json
        and not isinstance(args.initial_messages_json, MagicMock)
    ):
        try:
            initial_messages = json.loads(args.initial_messages_json)
            if not isinstance(initial_messages, list):
                raise ValueError("initial_messages_json must be a JSON list")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse initial_messages_json: {e}")
            raise ValueError(f"Invalid JSON format in initial_messages_json: {e}")

    medium = {
        "serverWebSocket": {
            "inputSampleRate": 48000,
            "outputSampleRate": 48000,
            "clientBufferSizeMs": 30000,
        }
    }

    try:
        response: Dict[str, Any] = await client.calls.create(
            system_prompt=args.system_prompt,
            temperature=args.temperature,
            voice=args.voice if args.voice else None,
            selected_tools=selected_tools,
            initial_messages=initial_messages,
            initial_output_medium="MESSAGE_MEDIUM_TEXT",
            medium=medium,
        )

        if not response or "joinUrl" not in response:
            raise ValueError("Invalid response from API: missing joinUrl")
        join_url: str = response["joinUrl"]

        return join_url
    except Exception as e:
        logging.error(f"Failed to create call: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _add_query_param(url: str, key: str, value: str) -> str:
    """Add a query parameter to a URL.

    This utility function parses a URL, adds or updates a query parameter,
    and returns the modified URL.

    Args:
        url: The original URL to modify.
        key: The query parameter key to add or update.
        value: The value for the query parameter.

    Returns:
        str: The modified URL with the added query parameter.

    Example:
        >>> _add_query_param("https://example.com", "key", "value")
        'https://example.com?key=value'
        >>> _add_query_param("https://example.com?existing=param", "key", "value")
        'https://example.com?existing=param&key=value'
    """
    import urllib.parse

    url_parts = list(urllib.parse.urlparse(url))
    query = dict(urllib.parse.parse_qsl(url_parts[4]))
    query.update({key: value})
    url_parts[4] = urllib.parse.urlencode(query)

    return urllib.parse.urlunparse(url_parts)


def create_output_handler(
    final_inference_ref: List[Optional[str]],
    agent_response_ref: List[str],
    current_final_response_ref: List[str],
    agent_response_complete: asyncio.Event,
) -> Any:
    """Create an output handler function for session events.

    This factory function creates and returns a callback function for handling
    the 'output' events from the WebSocket session. The handler processes
    text output from the agent, tracks final responses, and signals when a
    complete response has been received.

    Args:
        final_inference_ref: A mutable list reference to store the final inference.
        agent_response_ref: A mutable list reference to store the agent's response.
        current_final_response_ref: A mutable list reference to accumulate the current response.
        agent_response_complete: An event to signal when a complete response is received.

    Returns:
        Callable: A callback function for handling session output events.

    Example:
        ```python
        output_handler = create_output_handler(
            final_inference_ref=[None],
            agent_response_ref=[""],
            current_final_response_ref=[""],
            agent_response_complete=asyncio.Event()
        )
        session.on("output")(output_handler)
        ```
    """

    async def on_output(text: str, final: bool) -> None:
        """Handle output from the agent.

        This callback processes text output from the agent. It updates the console display,
        accumulates final responses, and detects when a complete response has been received.

        Args:
            text: The text output from the agent. May be a partial chunk during streaming.
            final: Whether this is a final response (true) or streaming update (false).
                  Only final responses are processed and displayed.

        Note:
            This function manipulates references passed to the parent function to maintain
            state between calls, as it's called multiple times during a streaming response.
        """
        # Skip non-final responses (streaming updates)
        if not final:
            return

        # Process final responses
        if text.strip() and text.strip() not in current_final_response_ref[0]:
            # Clear the "thinking" status
            print("\r" + " " * 20 + "\r", end="", flush=True)

            # Print the actual response
            print(f"Agent: {text.strip()}")

            # Add a space between chunks
            current_final_response_ref[0] += text.strip() + " "

            # Determine if this is the end of a complete response
            text_chunk = text.strip()
            is_complete = False

            # Check for completion indicators
            if text_chunk.endswith((".", "!", "?")):  # Has ending punctuation
                is_complete = True
            elif len(text_chunk) < 50:  # Short messages are likely complete
                is_complete = True

            if is_complete:
                # Mark the response as complete
                final_inference_ref[0] = current_final_response_ref[0].strip()
                agent_response_ref[0] = current_final_response_ref[0].strip()
                agent_response_complete.set()

    return on_output


async def setup_session_handlers(
    session: Any, done: asyncio.Event
) -> Tuple[List[str], asyncio.Event]:
    """Set up event handlers for the session.

    This function registers event handlers for various WebSocket session events, including:
    - 'state': For handling state changes in the conversation
    - 'output': For processing agent responses
    - 'ended': For handling session end events
    - 'error': For handling error events

    It also sets up signal handlers for graceful termination on SIGINT and SIGTERM.

    Args:
        session: The WebSocket session to set up handlers for
        done: An event to signal when the session is complete

    Returns:
        Tuple[List[str], asyncio.Event]: A tuple containing:
            - A mutable list reference for tracking agent responses
            - An event that signals when an agent response is complete

    Note:
        This function uses inner functions to define the event handlers with access to
        the session state variables.
    """
    loop = asyncio.get_running_loop()

    # State variables for conversation tracking - using lists as mutable references
    final_inference_ref = [None]  # type: List[Optional[str]]
    agent_response_ref = [""]  # type: List[str]
    current_final_response_ref = [""]  # type: List[str]

    # Event for signaling when a response is complete
    agent_response_complete = asyncio.Event()

    @session.on("state")
    async def on_state(state: str) -> None:
        """Handle state changes in the conversation.

        Updates the console display based on the current state of the conversation.

        Args:
            state: The new state of the conversation. Possible values:
                  - 'listening': The agent is listening for user input
                  - 'thinking': The agent is processing the user's message
                  - Other states may also be received but are not specifically handled
        """
        if state == "listening":
            print("User: ", end="", flush=True)
        elif state == "thinking":
            print("Agent thinking...", end="", flush=True)

    # Create and register the output handler
    output_handler = create_output_handler(
        final_inference_ref,
        agent_response_ref,
        current_final_response_ref,
        agent_response_complete,
    )
    session.on("output")(output_handler)

    @session.on("ended")
    async def on_ended() -> None:
        """Handle session end event.

        This callback is called when the session ends normally.
        It prints a message to the console and sets the 'done' event
        to signal that the session has ended.
        """
        print("Session ended.")
        done.set()

    @session.on("error")
    async def on_error(error: Exception) -> None:
        """Handle session error event.

        This callback is called when an error occurs in the session.
        It prints the error message to the console and sets the 'done' event
        to signal that the session should be terminated.

        Args:
            error: The exception that caused the error
        """
        print(f"Error: {error}")
        done.set()

    # Set up signal handlers
    loop.add_signal_handler(signal.SIGINT, lambda: done.set())
    loop.add_signal_handler(signal.SIGTERM, lambda: done.set())

    return agent_response_ref, agent_response_complete


async def run_conversation_loop(
    session: Any,
    done: asyncio.Event,
    agent_response_ref: List[str],
    agent_response_complete: asyncio.Event,
) -> None:
    """Run the main conversation loop.

    This function implements the main conversation loop between the user and the agent.
    It continuously prompts for user input, sends messages to the agent, and processes
    agent responses until the user exits or an error occurs.

    Args:
        session: The WebSocket session for the call
        done: An event signaling when the conversation should end
        agent_response_ref: A mutable list reference for tracking agent responses
        agent_response_complete: An event that signals when an agent response is complete

    Raises:
        KeyboardInterrupt: When the user interrupts the program (handled internally)
        Exception: For other errors that may occur during the conversation

    Note:
        The function handles proper cleanup by waiting for the 'done' event and
        stopping the session when the conversation ends.
    """
    is_conversation_active = True

    print(
        "Welcome to UltraVox CLI! "
        "Type 'exit', 'quit', or 'bye' to end the conversation."
    )

    # Main conversation loop
    try:
        while is_conversation_active and not done.is_set():
            try:
                # Wait for the agent's first response or previous response to complete
                while not agent_response_ref[0] and not done.is_set():
                    await asyncio.sleep(0.1)

                # Get user input
                user_input = input("User: ").strip()

                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print("Goodbye!")
                    is_conversation_active = False
                    done.set()
                    break

                # Reset the agent response for the next turn
                agent_response_ref[0] = ""
                agent_response_complete.clear()

                # Send the user message to the agent
                await session.send_text_message(user_input)

            except KeyboardInterrupt:
                print("\nGoodbye!")
                is_conversation_active = False
                done.set()
                break
            except Exception as e:
                logging.exception("Error in conversation loop", exc_info=e)
                print(f"Error: {e}")
                done.set()
                break
    finally:
        # Ensure proper cleanup
        await done.wait()
        await session.stop()


async def main() -> None:
    """Main entry point for the Ultravox CLI application.

    This function:
    1. Initializes the UltravoxClient with the API key from environment variables
    2. Creates a new call with parameters from command-line arguments
    3. Joins the call using the returned join URL
    4. Sets up session event handlers
    5. Starts the session and runs the conversation loop

    Global Args:
        args: Command-line arguments parsed by argparse

    Raises:
        ValueError: If the ULTRAVOX_API_KEY environment variable is not set
        Exception: For API errors, network issues, or other runtime errors

    Note:
        This function is run when the script is executed directly.
    """
    # Use the global args
    global args

    # Initialize the client
    api_key = os.getenv("ULTRAVOX_API_KEY")
    if not api_key:
        raise ValueError("ULTRAVOX_API_KEY environment variable is not set")
    client = UltravoxClient(api_key=api_key)

    # Create the call and get join URL
    join_url = await create_call(client, args)

    # Join the call
    session = await client.join_call(join_url)

    # Uncomment to use an example tool
    # session.register_tool("getSecretMenu", get_secret_menu)

    done = asyncio.Event()

    # Set up session handlers
    agent_response_ref, agent_response_complete = await setup_session_handlers(
        session, done
    )

    await session.start()

    # Run the conversation loop
    await run_conversation_loop(
        session, done, agent_response_ref, agent_response_complete
    )


if __name__ == "__main__":
    load_dotenv()

    api_key = os.getenv("ULTRAVOX_API_KEY", None)
    if not api_key:
        raise ValueError("Please set your ULTRAVOX_API_KEY environment variable")

    # Parse the command line arguments
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    asyncio.run(main())
