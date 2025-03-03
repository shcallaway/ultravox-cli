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
You are a friendly assistant. Local time is currently: ${datetime.datetime.now().isoformat()}
The user is talking to you over voice on their phone, and your response will be read out
loud with realistic text-to-speech (TTS) technology.
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


# This is an example tool implementation to demonstrate how to create and use tools with Ultravox
# It shows a pattern for implementing a simple tool that returns structured data
# In a real application, you would implement your own tools that provide actual functionality
async def get_secret_menu(parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handler for the getSecretMenu tool.

    This is an example tool that demonstrates how to implement a tool that returns structured data.
    The tool returns a mock "secret menu" with items and prices.
    In a real application, you might fetch this data from a database or API.
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
    """Creates a new call and returns its join URL."""
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
    if hasattr(args, 'initial_messages_json') and args.initial_messages_json and not isinstance(args.initial_messages_json, MagicMock):
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
    """Add a query parameter to a URL."""
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
    """Create an output handler function for session events."""

    async def on_output(text: str, final: bool) -> None:
        """Handle output from the agent.

        Args:
            text: The text output from the agent
            final: Whether this is a final response or not
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
    """Set up event handlers for the session."""
    loop = asyncio.get_running_loop()

    # State variables for conversation tracking - using lists as mutable references
    final_inference_ref = [None]  # type: List[Optional[str]]
    agent_response_ref = [""]  # type: List[str]
    current_final_response_ref = [""]  # type: List[str]

    # Event for signaling when a response is complete
    agent_response_complete = asyncio.Event()

    @session.on("state")
    async def on_state(state: str) -> None:
        """Handle state changes in the conversation."""
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
        """Handle session end event."""
        print("Session ended.")
        done.set()

    @session.on("error")
    async def on_error(error: Exception) -> None:
        """Handle session error event."""
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
    """Run the main conversation loop."""
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
