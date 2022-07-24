# The Game (working title)

## Getting started

Install the dependencies:
```sh
poetry install --no-dev
```

Start the server:
```sh
poetry run python the_game/server.py
```

Connect to the server:
```sh
poetry run python -m websockets "ws://localhost:8001"
```

## Development Setup

This project uses `poetry` for package management. See the [Poetry installation docs](https://python-poetry.org/docs/#installation) to install it. Once installed, run `poetry install` to install the project dependencies.

Please also [install](https://pre-commit.com/#install) `pre-commit` to automatically lint your commits. Run `pre-commit install` to initialize the pre-commit hooks in your repo.
