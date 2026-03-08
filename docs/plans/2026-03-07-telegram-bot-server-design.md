# MLBB Telegram Bot Server Design

## Overview

A Python Telegram bot server that receives commands via webhook, maps them to skill prompt templates, and executes them through a pluggable AI agent backed by MCP tools. The AI agent uses the existing `mlbb_mcp` server to retrieve Mobile Legends: Bang Bang game data.

## Architecture

```
Telegram User
    │ webhook (HTTPS)
    ▼
mlbb_bot_server (python-telegram-bot)
    │
    ├── handlers.py     ← parses command, loads skill template
    ├── agent/          ← pluggable AI agent layer
    │   ├── base.py     ← abstract AgentClient interface
    │   └── claude.py   ← Claude Agent SDK implementation
    │
    ▼
Claude Agent (via Agent SDK)
    │ MCP (stdio)
    ▼
mlbb_mcp server
    ├── get_hero_list
    └── get_hero_detail
```

### Three Layers

1. **Telegram layer** — `python-telegram-bot` handles webhook, parses commands, sends responses
2. **Agent layer** — Pluggable AI agent interface; default implementation uses Claude Agent SDK with MCP
3. **Data layer** — Existing `mlbb_mcp` server provides hero data tools via MCP stdio

## Scope

**In scope (v1):**
- `/team_counter` command — user provides enemy hero lineup, bot suggests counter picks
- Webhook mode for receiving Telegram updates
- Rich Telegram HTML output (formatted by Claude via skill prompt instructions)
- Pluggable agent backend (abstract interface + Claude implementation)
- 100% test coverage

**Out of scope (future):**
- Additional commands (`/hero_info`, `/hero_list`, etc.)
- Long-polling mode
- Conversation state / multi-turn interactions
- User authentication or rate limiting

## Project Structure

```
mlbb_bot_server/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Entry point: webhook setup, Application init
│   └── handlers.py          # Telegram command handlers (arg parsing, send response)
├── agent/
│   ├── __init__.py
│   ├── base.py              # Abstract AgentClient interface
│   └── claude.py            # Claude Agent SDK implementation
├── skills/
│   └── team_counter.md  # Prompt template with formatting instructions
├── config.py                # Settings: load .env, command-to-skill mapping
├── pyproject.toml
├── .env.example
├── tests/
│   ├── __init__.py
│   ├── test_handlers.py
│   ├── test_agent_client.py
│   ├── test_config.py
│   └── test_main.py
└── docs/
    └── plans/
```

## Command Flow

1. User sends `/team_counter Lancelot, Pharsa, Tigreal, Bruno, Rafaela`
2. `handlers.py` parses the command, extracts hero names as a comma-separated string
3. `handlers.py` loads `skills/team-counter/SKILL.md`, interpolates `{heroes}` placeholder
4. `agent/client.py` calls the configured agent with the interpolated prompt
5. Claude agent autonomously calls `get_hero_list` / `get_hero_detail` via MCP as needed
6. Claude formats the response as Telegram HTML (as instructed in the skill template)
7. `handlers.py` sends Claude's result directly to Telegram with `parse_mode="HTML"`

## Components

### `config.py`

Loads environment variables from `.env` via `python-dotenv`. Defines the command registry:

```python
COMMANDS = {
    "/team_counter": {
        "skill_file": "skills/team-counter/SKILL.md",
        "description": "Suggest counter heroes for an enemy lineup",
        "args": ["heroes"],
    }
}
```

Also defines which agent backend to use via `AGENT_BACKEND` env var (default: `claude`).

### `agent/base.py`

Abstract base class defining the agent interface:

```python
class AgentClient(ABC):
    @abstractmethod
    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt to the agent and return the text response."""
        ...
```

Any AI agent can be swapped in by implementing this interface.

### `agent/claude.py`

Claude Agent SDK implementation of `AgentClient`:

- Uses `query()` with `mcp_servers` config pointing to `mlbb_mcp.server` via stdio
- `permission_mode="bypassPermissions"` (server-side, no human in loop)
- `allow_dangerously_skip_permissions=True`
- `max_turns=10` to prevent runaway loops
- `max_budget_usd=0.05` per request as a safety cap
- Model: `claude-haiku-4-5` (fast and cost-effective for bot responses)

### `skills/team-counter/SKILL.md`

Prompt template file containing:
- Task instructions (analyze lineup, suggest counters)
- `{heroes}` placeholder for interpolation
- Telegram HTML output format instructions (bold, line breaks, structure)

Claude uses MCP tools as needed and outputs a ready-to-send Telegram HTML message.

### `bot/handlers.py`

- Registers `/team_counter` command handler
- Parses hero names from command arguments
- Loads and interpolates the skill template
- Calls the agent, sends result to user
- Handles errors (missing args, agent failures) with user-friendly messages

### `bot/main.py`

- Creates `python-telegram-bot` `Application`
- Registers command handlers
- Sets up webhook on configured URL and port
- Entry point: `python -m bot.main`

## Dependencies

- `python-telegram-bot[webhooks]` — Telegram bot framework with webhook support
- `claude-agent-sdk` — Claude Agent SDK for Python
- `python-dotenv` — Environment variable loading from `.env`
- `pytest` + `pytest-asyncio` + `pytest-cov` — Testing with async support and coverage

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot API token | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | Yes |
| `WEBHOOK_URL` | Public HTTPS URL for webhook | Yes |
| `WEBHOOK_PORT` | Port for webhook server | Yes (default: 8443) |
| `AGENT_BACKEND` | Agent implementation to use | No (default: `claude`) |

## Error Handling

- **Missing command args** — Reply with usage instructions
- **Agent SDK errors** (CLI not found, connection) — Reply "Service temporarily unavailable"
- **MCP/API errors** — Claude handles gracefully, bot forwards the response
- **Agent timeout** — `max_turns` cap prevents infinite loops
- **Telegram rate limits** — `python-telegram-bot` handles retries internally

## Testing

- 100% test coverage required
- Agent layer tested with mock implementations of `AgentClient`
- Telegram handlers tested with `python-telegram-bot` test utilities
- Skill template loading tested with filesystem fixtures
- Config tested with mock environment variables
