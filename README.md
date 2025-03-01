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

4. Run the CLI:

```bash
python cli.py
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

## Usage

Once the CLI is running, you can interact with the Ultravox agent:

```
$ python cli.py
Welcome to Ultravox CLI!
> hello
Agent: Hello! How can I assist you today?
> tell me about the weather
Agent: I don't have real-time weather data. Would you like me to explain how to get weather information?
> exit
Goodbye!
```

Common commands:

- `exit` or `quit` - Exit the CLI
- `help` - Show available commands
- `restart` - Start a new conversation

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
