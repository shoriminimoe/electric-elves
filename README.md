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

Now in a separate terminal, launch the client:

```sh
poetry run python the_game/client.py
```

## Development

### Setup

This project uses `poetry` for package management. See the [Poetry installation docs](https://python-poetry.org/docs/#installation) to install it. Once installed, run `poetry install` to install the project dependencies.

Please also [install](https://pre-commit.com/#install) `pre-commit` to automatically lint your commits. Run `pre-commit install` to initialize the pre-commit hooks in your repo.

### Message debugging

You can debug messages by connecting a client to the server and manually entering messages. First start the server as in the [getting started](#getting-started) section. Then connect to the server like this:

```sh
poetry run python -m websockets "ws://localhost:8001"
```

Now send a message:

```sh
Connected to ws://localhost:8001.
> {"type": 1, "content": "bwah"}
< bwah
>

```

> :information_source: Note
>
> The types of available messages are defined in the `messaging.MessageType` enum. When the enum is serialized, its integer value is used. Keep that in mind when communicating with the server this way.

This is what the server reports:

```sh
[2022-07-26 09:53:44] INFO server listening on [::]:8001
[2022-07-26 09:53:44] INFO server listening on 0.0.0.0:8001
[2022-07-26 09:54:02] INFO connection open
[2022-07-26 09:54:20] INFO message from 4a68457c-12fc-4184-873a-103b30f3784e: {"type": 1, "content": "bwah"}
[2022-07-26 09:54:20] INFO Creating new Message from message: {"type": 1, "content": "bwah"}
```
