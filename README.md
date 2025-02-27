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
