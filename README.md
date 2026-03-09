# MLBB Bot Server

A Telegram bot that suggests Mobile Legends: Bang Bang heroes based on your team lineup. Powered by Claude AI and the MLBB MCP server.

## What it does

Send `/suggest_heroes` to the bot and it walks you through a two-step conversation:

1. Enter your team lineup (1–5 heroes, comma-separated)
2. Enter the enemy team lineup, or type `skip`

The bot then queries hero data via the MLBB MCP server, analyzes counters and team synergy, and returns 3–5 suggested heroes with reasoning.

## Setup

**Requirements:** Python 3.14+, the `claude` CLI installed and authenticated.

```bash
pip install -e .
```

Create a `.env` file:

```
TELEGRAM_BOT_TOKEN=your_token_here
```

## Running the server

```bash
python3 -m bot.main
```

## Running tests

```bash
# Full suite with coverage
python3 -m pytest

# Single test
python3 -m pytest tests/test_handlers.py::TestSuggestHeroesEnemyTeam::test_valid_lineup_calls_agent -v
```

Coverage is enforced at 100%.
