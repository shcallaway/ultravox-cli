# Ultravox CLI

A simple CLI that allows you to "chat" with an Ultravox voice agent. See Ultravox documentation [here](https://www.ultravox.ai/).

Ultravox is an AI voice agent platform that enables natural and engaging voice conversations. This CLI tool provides a simple interface to interact with Ultravox agents directly from your terminal.

## Prerequisites

- Python 3.10+
- pip
- Ultravox API key (obtain from [Ultravox dashboard](https://www.ultravox.ai/))
- Microphone hardware (for voice input)
- Speaker/headphones (for voice output)

## Setup

1. Create a virtual environment:

```bash
python -m venv venv

# If this doesn't work, try:
python3 -m venv venv
```

2. Activate the virtual environment:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install the package:

```bash
pip install -e .
```

5. Run the CLI:

```bash
python ultravox_cli/cli.py
```

You can cleanup/reset your virtual environment by running:

```bash
deactivate
rm -rf venv
```

## Configuration

Create a `.env` file in the project root with your Ultravox API credentials:

```
ULTRAVOX_API_KEY=your_api_key_here
ULTRAVOX_AGENT_ID=your_agent_id_here
```

## Features

### Multi-turn Conversations

The CLI now supports multi-turn conversations with UltraVox agents! This means you can have continuous, back-and-forth dialog with the agent without having to restart the session after each exchange.

#### How it works

- When the CLI starts, it displays the agent's initial greeting.
- You can then type your message and press Enter to send it to the agent.
- The agent responds, and you can continue the conversation with another message.
- The conversation loop continues until you type an exit command like "exit", "quit", or "bye".

#### Technical Implementation

The multi-turn conversation feature is implemented using UltraVox's `inputTextMessage` API endpoint. Each user message is sent as a structured payload following the UltraVox schema, which includes:

- The text message content
- The conversation session information
- Required identifiers for message tracking

Behind the scenes, the CLI maintains the WebSocket connection with the UltraVox agent throughout the entire conversation, enabling a seamless dialog experience.

## CLI Options

The CLI supports the following command-line options:

- `--verbose` or `-v`: Show verbose session information
- `--voice` or `-V`: Specify the name or ID of the voice to use
- `--system-prompt`: Custom system prompt to use for the call (defaults to a basic Dr. Donut prompt)
- `--temperature`: Temperature to use when creating the call (defaults to 0.8)
- `--initial-messages-json`: JSON string containing a list of initial messages to be provided to the call

Example usage with options:

```bash
python ultravox_cli/cli.py --voice claude --temperature 0.7 --initial-messages-json '[{"role":"MESSAGE_ROLE_AGENT","text":"Welcome to our service!"},{"role":"MESSAGE_ROLE_USER","text":"Tell me about your offerings"}]'
```

## Usage

Once the CLI is running, you can interact with the Ultravox agent in a multi-turn conversation:

```
$ python cli.py
Welcome to UltraVox CLI! Type 'exit', 'quit', or 'bye' to end the conversation.
Agent: Hello! How can I assist you today?
User: hello
Agent: Hello! How can I assist you today?
User: tell me about the weather
Agent: I don't have real-time weather data. Would you like me to explain how to get weather information?
User: yes please
Agent: To get weather information, you can use weather websites like Weather.com or AccuWeather,
download weather apps on your smartphone, or check local news websites. Many digital assistants
like Siri or Google Assistant can also provide weather forecasts when asked. Would you like to
know about any specific weather service?
User: no thanks, that's helpful
Agent: You're welcome! I'm glad I could help. If you have any other questions, feel free to ask.
User: exit
Goodbye!
Session ended.
```

The CLI now supports continuous conversation with the agent until you decide to exit.

Exit commands:

- `exit` - Exit the conversation
- `quit` - Exit the conversation
- `bye` - Exit the conversation

## Development

// ... existing code ...
