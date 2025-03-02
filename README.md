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

To run the tests:

```bash
python -m pytest
```

To run the linter:

```bash
python -m flake8
```

To run the type checker:

```bash
python -m mypy .
```

To format the code:

```bash
python -m black .
```

## Troubleshooting

- **API Connection Issues**: Verify your internet connection and API credentials
- **Microphone Not Working**: Check your system's audio input settings
- **Python Version Errors**: Ensure you're using Python 3.10 or later

### Community

- Report issues on [GitHub Issues](https://github.com/yourusername/ultravox-cli/issues)
- Contribute to discussions in the [Discussions tab](https://github.com/yourusername/ultravox-cli/discussions)
- Share your use-cases with the community
- Contact maintainers through GitHub or the Ultravox community channels

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). This means:

- You can use this software for any purpose
- You can modify and distribute this software
- If you distribute modified versions, they must also be under GPLv3
- All changes must be documented and source code must be available

See the [LICENSE](LICENSE) file for the complete license text.
