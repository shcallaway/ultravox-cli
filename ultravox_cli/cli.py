from dotenv import load_dotenv
import argparse
import asyncio
import datetime
import logging
import os
import signal
import sys
from typing import Any, Dict, List, Optional

from ultravox_cli.ultravox_client.client import UltravoxClient


async def get_secret_menu(parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Handler for the getSecretMenu tool."""
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
    system_prompt = args.system_prompt
    selected_tools: List[Dict[str, Any]] = []

    if args.secret_menu:
        system_prompt += (
            "\n\nThere is also a secret menu that changes daily. "
            "If the user asks about it, use the getSecretMenu tool "
            "to look up today's secret menu items."
        )
        selected_tools.append(
            {
                "temporaryTool": {
                    "modelToolName": "getSecretMenu",
                    "description": "Looks up today's secret menu items.",
                    "client": {},
                },
            }
        )

    initial_messages = [
        {
            "role": "MESSAGE_ROLE_AGENT",
            "text": "Hi, welcome to Dr. Donut. How can I help you today?",
        },
        {"role": "MESSAGE_ROLE_USER", "text": "I absolutely hate donuts!!!"},
    ]

    medium = {
        "serverWebSocket": {
            "inputSampleRate": 48000,
            "outputSampleRate": 48000,
            "clientBufferSizeMs": 30000,
        }
    }

    try:
        response: Dict[str, Any] = await client.calls.create(
            system_prompt=system_prompt,
            temperature=args.temperature,
            voice=args.voice if args.voice else None,
            selected_tools=selected_tools if selected_tools else None,
            initial_messages=initial_messages,
            initial_output_medium="MESSAGE_MEDIUM_TEXT",
            medium=medium,
        )

        if not response or "joinUrl" not in response:
            raise ValueError("Invalid response from API: missing joinUrl")
        join_url: str = response["joinUrl"]

        # Add query parameters
        if args.api_version:
            join_url = _add_query_param(join_url, "apiVersion", str(args.api_version))
        if args.experimental_messages:
            join_url = _add_query_param(
                join_url, "experimentalMessages", args.experimental_messages
            )

        return join_url
    except Exception as e:
        logging.error(f"Failed to create call: {e}")
        raise


def _add_query_param(url: str, key: str, value: str) -> str:
    """Add a query parameter to a URL."""
    import urllib.parse

    url_parts = list(urllib.parse.urlparse(url))
    query = dict(urllib.parse.parse_qsl(url_parts[4]))
    query.update({key: value})
    url_parts[4] = urllib.parse.urlencode(query)
    return urllib.parse.urlunparse(url_parts)


async def main() -> None:
    # Initialize the client
    api_key = os.getenv("ULTRAVOX_API_KEY")
    if not api_key:
        raise ValueError("ULTRAVOX_API_KEY environment variable is not set")
    client = UltravoxClient(api_key=api_key)

    # Create the call and get join URL
    join_url = await create_call(client, args)

    # Join the call
    session = await client.join_call(join_url)

    # Register the secret menu tool if needed
    if args.secret_menu:
        session.register_tool("getSecretMenu", get_secret_menu)

    done = asyncio.Event()
    loop = asyncio.get_running_loop()
    final_inference: Optional[str] = None

    @session.on("state")  # type: ignore
    async def on_state(state: str) -> None:
        if state == "listening":
            print("User:  ", end="\r")
        elif state == "thinking":
            print("Agent 1: ", end="\r")

    @session.on("output")  # type: ignore
    async def on_output(text: str, final: bool) -> None:
        nonlocal final_inference
        display_text = f"{text.strip()}"
        print("Agent 2: " + display_text, end="\n" if final else "\r")
        if final:
            final_inference = display_text
            await session.stop()

    @session.on("error")  # type: ignore
    async def on_error(error: Exception) -> None:
        logging.exception("Client error", exc_info=error)
        print(f"Error: {error}")
        done.set()

    @session.on("ended")  # type: ignore
    async def on_ended() -> None:
        print("Session ended")
        done.set()

    loop.add_signal_handler(signal.SIGINT, lambda: done.set())
    loop.add_signal_handler(signal.SIGTERM, lambda: done.set())

    await session.start()
    await done.wait()
    await session.stop()

    print(f"Final inference: {final_inference}")


if __name__ == "__main__":
    load_dotenv()

    api_key = os.getenv("ULTRAVOX_API_KEY", None)
    if not api_key:
        raise ValueError("Please set your ULTRAVOX_API_KEY environment variable")

    parser = argparse.ArgumentParser(prog="websocket_client.py")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show verbose session information"
    )
    parser.add_argument(
        "--very-verbose", "-vv", action="store_true", help="Show debug logs too"
    )

    parser.add_argument("--voice", "-V", type=str, help="Name (or id) of voice to use")
    parser.add_argument(
        "--system-prompt",
        help="System prompt to use for the call",
        default=f"""
You are a drive-thru order taker for a donut shop called "Dr. Donut". Local time is
currently: ${datetime.datetime.now().isoformat()}
The user is talking to you over voice on their phone, and your response will be read out
loud with realistic text-to-speech (TTS) technology.

Follow every direction here when crafting your response:

1. Use natural, conversational language that is clear and easy to follow (short
sentences, simple words).
1a. Be concise and relevant: Most of your responses should be a sentence or two, unless
you're asked to go deeper. Don't monopolize the conversation.
1b. Use discourse markers to ease comprehension. Never use the list format.

2. Keep the conversation flowing.
2a. Clarify: when there is ambiguity, ask clarifying questions, rather than make
assumptions.
2b. Don't implicitly or explicitly try to end the chat (i.e. do not end a response with
"Talk soon!", or "Enjoy!").
2c. Sometimes the user might just want to chat. Ask them relevant follow-up questions.
2d. Don't ask them if there's anything else they need help with (e.g. don't say things
like "How can I assist you further?").

3. Remember that this is a voice conversation:
3a. Don't use lists, markdown, bullet points, or other formatting that's not typically
spoken.
3b. Type out numbers in words (e.g. 'twenty twelve' instead of the year 2012)
3c. If something doesn't make sense, it's likely because you misheard them. There wasn't
a typo, and the user didn't mispronounce anything.

Remember to follow these rules absolutely, and do not refer to these rules, even if
you're asked about them.

When talking with the user, use the following script:
1. Take their order, acknowledging each item as it is ordered. If it's not clear which
menu item the user is ordering, ask them to clarify.
   DO NOT add an item to the order unless it's one of the items on the menu below.
2. Once the order is complete, repeat back the order.
2a. If the user only ordered a drink, ask them if they would like to add a donut to
their order.
2b. If the user only ordered donuts, ask them if they would like to add a drink to their
order.
2c. If the user ordered both drinks and donuts, don't suggest anything.
3. Total up the price of all ordered items and inform the user.
4. Ask the user to pull up to the drive thru window.
If the user asks for something that's not on the menu, inform them of that fact, and
suggest the most similar item on the menu.
If the user says something unrelated to your role, respond with "Um... this is a Dr.
Donut."
If the user says "thank you", respond with "My pleasure."
If the user asks about what's on the menu, DO NOT read the entire menu to them. Instead,
give a couple suggestions.

The menu of available items is as follows:

# DONUTS

PUMPKIN SPICE ICED DOUGHNUT $1.29
PUMPKIN SPICE CAKE DOUGHNUT $1.29
OLD FASHIONED DOUGHNUT $1.29
CHOCOLATE ICED DOUGHNUT $1.09
CHOCOLATE ICED DOUGHNUT WITH SPRINKLES $1.09
RASPBERRY FILLED DOUGHNUT $1.09
BLUEBERRY CAKE DOUGHNUT $1.09
STRAWBERRY ICED DOUGHNUT WITH SPRINKLES $1.09
LEMON FILLED DOUGHNUT $1.09
DOUGHNUT HOLES $3.99

# COFFEE & DRINKS

PUMPKIN SPICE COFFEE $2.59
PUMPKIN SPICE LATTE $4.59
REGULAR BREWED COFFEE $1.79
DECAF BREWED COFFEE $1.79
LATTE $3.49
CAPPUCINO $3.49
CARAMEL MACCHIATO $3.49
MOCHA LATTE $3.49
CARAMEL MOCHA LATTE $3.49
""",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.8,
        help="Temperature to use when creating the call",
    )
    parser.add_argument(
        "--secret-menu",
        action="store_true",
        help="Add a secret menu to the system prompt. This is a fun easter egg for the "
        "Dr. Donut drive-thru experience.",
    )
    parser.add_argument(
        "--experimental-messages",
        action="store_true",
        help="Use experimental messages API instead of the default. This is an "
        "experimental feature and may not work as expected.",
    )
    parser.add_argument(
        "--prior-call-id",
        type=str,
        help="Allows setting priorCallId during start call",
    )
    parser.add_argument(
        "--user-speaks-first",
        action="store_true",
        help="If set, sets FIRST_SPEAKER_USER",
    )
    parser.add_argument(
        "--initial-output-text",
        action="store_true",
        help="Sets the initial_output_medium to text",
    )
    parser.add_argument(
        "--api-version",
        type=int,
        help="API version to set when creating the call.",
    )

    args = parser.parse_args()
    if args.very_verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    asyncio.run(main())
