# Ultravox CLI

A simple CLI that allows you to "chat" with an Ultravox voice agent. See Ultravox documentation [here](https://www.ultravox.ai/).

## Prerequisites

- Python 3.10+
- pip

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

## Development

To run the tests:

```bash
pytest
```

To run the linter:

```bash
flake8
```

To run the type checker:

```bash
mypy
```

To format the code:

```bash
black
```

### Community

- Report issues on GitHub
- Contribute to discussions
- Share your use-cases

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3). This means:

- You can use this software for any purpose
- You can modify and distribute this software
- If you distribute modified versions, they must also be under GPLv3
- All changes must be documented and source code must be available

See the [LICENSE](LICENSE) file for the complete license text.
