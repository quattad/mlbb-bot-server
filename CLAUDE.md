# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests with coverage
python3 -m pytest

# Run a single test
python3 -m pytest tests/test_handlers.py::TestSuggestHeroesEnemyTeam::test_valid_lineup_calls_agent -v

# Run the bot
python3 -m bot.main
```

Coverage is enforced at 100% (`fail_under = 100`). Every new code path needs a test.

## Architecture

The bot is a Python Telegram Bot (v22) that acts as a thin dispatcher: it collects user input via a multi-step `ConversationHandler`, renders a skill prompt template, and delegates reasoning to a Claude subprocess via the `AgentClient` interface.

### Request flow

```
Telegram → bot/handlers.py (ConversationHandler) → bot/skills.py (load_skill) → agent/claude.py (subprocess) → Claude CLI + MLBB MCP server
```

### Key modules

- **`config.py`** — `load_config()` reads `.env`, returns a `Config` dataclass. `COMMANDS` dict maps command names to `skill_file`, `description`, and `args`. Adding a new command means adding an entry here and a handler builder in `bot/handlers.py`.

- **`bot/handlers.py`** — All Telegram handler logic. `build_handlers(agent, commands)` returns a `list[ConversationHandler]`. The `/suggest_heroes` flow is a two-state conversation: `USER_TEAM (0)` → `ENEMY_TEAM (1)` → `END`. State is stored in `context.user_data["user_lineup"]`. 5-minute timeout via `_TIMEOUT_SECONDS`.

- **`bot/skills.py`** — `load_skill(path, **kwargs)` reads a Markdown skill file and calls `.format(**kwargs)` on it. Skill files use `{placeholder}` syntax.

- **`agent/base.py`** — `AgentClient` ABC with a single `async run(prompt, system_prompt) -> str` method.

- **`agent/claude.py`** — `ClaudeAgentClient` spawns a `claude` subprocess with `--print`, `--dangerously-skip-permissions`, `--add-dir <skills_dir>`, and an inline MCP config pointing at `mlbb_mcp.server`.

- **`skills/suggest-heroes/SKILL.md`** — Prompt template with `{user_heroes}` and `{enemy_heroes}` placeholders. The agent uses the MLBB MCP server to fetch hero data and suggest 3–5 heroes. `enemy_heroes` is the string `"None"` when the user skipped.

### Environment

```
TELEGRAM_BOT_TOKEN=   # required
AGENT_BACKEND=claude  # optional, default: claude
```

### Adding a new bot command

1. Add an entry to `COMMANDS` in `config.py` with `skill_file`, `description`, and `args`.
2. Create the skill file at `skills/<name>/SKILL.md`.
3. Add a handler builder lambda to `handler_builders` in `build_handlers` in `bot/handlers.py`.
4. Add tests in `tests/test_handlers.py` and update `tests/test_config.py`.
