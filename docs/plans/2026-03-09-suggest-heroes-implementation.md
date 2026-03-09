# Suggest Heroes Multi-Step Conversation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the single-message `/team_counter` command with a multi-step `/suggest_heroes` conversation using `ConversationHandler`, with full rename of all `team_counter`/`team-counter` references.

**Architecture:** Uses python-telegram-bot's `ConversationHandler` for multi-step state management with two states (`USER_TEAM`, `ENEMY_TEAM`). Each state handler is a standalone async function that validates input, stores state in `context.user_data`, and returns the next state. `build_handlers` returns handler objects directly instead of `(name, fn)` tuples.

**Tech Stack:** python-telegram-bot v22 (`ConversationHandler`, `CommandHandler`, `MessageHandler`, `filters`), pytest with pytest-asyncio, 100% coverage required.

---

### Task 1: Rename skill directory and update SKILL.md

**Files:**
- Rename: `skills/team-counter/` → `skills/suggest-heroes/`
- Modify: `skills/suggest-heroes/SKILL.md`

**Step 1: Rename the directory**

```bash
mv skills/team-counter skills/suggest-heroes
```

**Step 2: Update SKILL.md content**

Replace the entire file with:

```markdown
---
name: suggest-heroes
description: Analyzes the hero lineup provided by the user and suggests heroes that the user can pick. Should be executed when the user input contains '/suggest_heroes'.
---

User team lineup: {user_heroes}
Enemy team lineup: {enemy_heroes}

# Overview
We want to analyze the hero details of the current team line-up provided by the user and propose 3-5 heroes to help the user increase his chances of winning.

## Process

**Querying Hero Information**
- Use the MLBB MCP server to fetch the hero details for all the heroes in both lineups.
- Verify that all heroes have data returned by the MCP server. If any of the heroes cannot be found using the MCP server, do NOT proceed and tell the user which heroes cannot be found.

**Analyzing the Hero Lineup**
- Use the hero data to analyze potential heroes that the user can pick to increase the chances of him winning the match.
- If an enemy team lineup is provided (enemy_heroes is not "None"):
  - You MUST use the enemy team's hero lineup to suggest heroes that have skills to counter the enemy heroes. This can be determined by checking the counter picks for the hero or heroes that have a high win rate against the given enemy hero.
  - You MUST use the user team's hero lineup to suggest heroes that have good synergy with the ones in the lineup. Do NOT suggest heroes that have already been chosen in the team.
- If no enemy team lineup is provided (enemy_heroes is "None"):
  - Suggest heroes based on team synergy with the user's existing lineup and general meta strength.
  - Focus on filling missing roles (tank, marksman, mage, assassin, support/roam) and complementing the team composition.

**Summarizing Suggestions**
- Provide a list of 3-5 suggested heroes to the user.
- For each suggested hero, the following information should be provided:
1. Hero name
2. Why the hero was suggested
3. Which enemy heroes the suggested hero counters (if enemy team was provided)
4. Which user team heroes the suggested hero would have good synergy with
```

**Step 3: Commit**

```bash
git add skills/
git commit -m "feat: rename team-counter skill to suggest-heroes, update to 3-5 heroes"
```

---

### Task 2: Update config.py

**Files:**
- Modify: `config.py:35-41`
- Test: `tests/test_config.py:51-66`

**Step 1: Write the failing tests**

Replace `TestCommandRegistry` in `tests/test_config.py` with:

```python
class TestCommandRegistry:
    def test_suggest_heroes_command_exists(self):
        assert "/suggest_heroes" in COMMANDS

    def test_suggest_heroes_has_skill_file(self):
        cmd = COMMANDS["/suggest_heroes"]
        assert cmd["skill_file"].endswith("skills/suggest-heroes/SKILL.md")

    def test_suggest_heroes_has_description(self):
        cmd = COMMANDS["/suggest_heroes"]
        assert "description" in cmd
        assert len(cmd["description"]) > 0

    def test_suggest_heroes_has_args(self):
        cmd = COMMANDS["/suggest_heroes"]
        assert cmd["args"] == ["heroes"]
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_config.py::TestCommandRegistry -v`
Expected: FAIL — `"/suggest_heroes"` not in `COMMANDS`

**Step 3: Update config.py**

Replace the `COMMANDS` dict (lines 35-41) with:

```python
COMMANDS: dict[str, dict] = {
    "/suggest_heroes": {
        "skill_file": str(_PROJECT_ROOT / "skills" / "suggest-heroes" / "SKILL.md"),
        "description": "Suggest heroes based on team lineup",
        "args": ["heroes"],
    }
}
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_config.py -v`
Expected: PASS (all 9 tests)

**Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: rename /team_counter to /suggest_heroes in config"
```

---

### Task 3: Rewrite bot/handlers.py with ConversationHandler

**Files:**
- Rewrite: `bot/handlers.py`
- Test: `tests/test_handlers.py`

**Step 1: Write the failing tests**

Replace the entire `tests/test_handlers.py` with:

```python
# tests/test_handlers.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from telegram.ext import ConversationHandler

from agent.base import AgentClient
from bot.handlers import (
    ENEMY_TEAM,
    USER_TEAM,
    _parse_lineup,
    build_handlers,
    suggest_heroes_enemy_team,
    suggest_heroes_start,
    suggest_heroes_timeout,
    suggest_heroes_user_team,
)


def _make_update_and_context(text: str = "", user_data: dict | None = None):
    """Create mock Telegram Update and Context."""
    update = MagicMock()
    update.effective_message.reply_html = AsyncMock()
    update.message.text = text
    context = MagicMock()
    context.user_data = user_data if user_data is not None else {}
    return update, context


class FakeAgent(AgentClient):
    def __init__(self, response: str = "mock response"):
        self.response = response
        self.last_prompt = None

    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        self.last_prompt = prompt
        return self.response


class TestParseLineup:
    def test_valid_single_hero(self):
        assert _parse_lineup("Lancelot") == ["Lancelot"]

    def test_valid_multiple_heroes(self):
        assert _parse_lineup("Lancelot, Pharsa, Fanny") == [
            "Lancelot",
            "Pharsa",
            "Fanny",
        ]

    def test_valid_five_heroes(self):
        result = _parse_lineup("A, B, C, D, E")
        assert len(result) == 5

    def test_strips_whitespace(self):
        assert _parse_lineup("  Lancelot ,  Pharsa  ") == ["Lancelot", "Pharsa"]

    def test_multi_word_hero_names(self):
        assert _parse_lineup("Yu Zhong, Sun Wukong") == ["Yu Zhong", "Sun Wukong"]

    def test_empty_string_returns_none(self):
        assert _parse_lineup("") is None

    def test_whitespace_only_returns_none(self):
        assert _parse_lineup("   ") is None

    def test_six_heroes_returns_none(self):
        assert _parse_lineup("A, B, C, D, E, F") is None

    def test_trailing_commas_ignored(self):
        assert _parse_lineup("Lancelot, Pharsa,") == ["Lancelot", "Pharsa"]


class TestSuggestHeroesStart:
    async def test_prompts_for_user_team(self):
        update, context = _make_update_and_context()

        result = await suggest_heroes_start(update, context)

        assert result == USER_TEAM
        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "team lineup" in reply_text.lower()


class TestSuggestHeroesUserTeam:
    async def test_valid_lineup_stores_and_prompts_enemy(self):
        update, context = _make_update_and_context("Lancelot, Pharsa")

        result = await suggest_heroes_user_team(update, context)

        assert result == ENEMY_TEAM
        assert context.user_data["user_lineup"] == ["Lancelot", "Pharsa"]
        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "enemy" in reply_text.lower()

    async def test_invalid_lineup_reprompts(self):
        update, context = _make_update_and_context("A, B, C, D, E, F")

        result = await suggest_heroes_user_team(update, context)

        assert result == USER_TEAM
        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "1" in reply_text and "5" in reply_text

    async def test_multi_word_hero_names_preserved(self):
        update, context = _make_update_and_context("Yu Zhong, Sun Wukong")

        result = await suggest_heroes_user_team(update, context)

        assert result == ENEMY_TEAM
        assert context.user_data["user_lineup"] == ["Yu Zhong", "Sun Wukong"]


class TestSuggestHeroesEnemyTeam:
    async def test_valid_lineup_calls_agent(self, tmp_path):
        skill_file = tmp_path / "skill.md"
        skill_file.write_text("User: {user_heroes} Enemy: {enemy_heroes}")

        agent = FakeAgent(response="<b>Pick Fanny</b>")
        handler = suggest_heroes_enemy_team(agent, str(skill_file))

        update, context = _make_update_and_context(
            "Fanny, Lancelot",
            user_data={"user_lineup": ["Zilong", "Ruby"]},
        )

        result = await handler(update, context)

        assert result == ConversationHandler.END
        update.effective_message.reply_html.assert_called_once_with("<b>Pick Fanny</b>")
        assert "Zilong" in agent.last_prompt
        assert "Fanny" in agent.last_prompt

    async def test_skip_calls_agent_with_none(self, tmp_path):
        skill_file = tmp_path / "skill.md"
        skill_file.write_text("User: {user_heroes} Enemy: {enemy_heroes}")

        agent = FakeAgent(response="synergy picks")
        handler = suggest_heroes_enemy_team(agent, str(skill_file))

        update, context = _make_update_and_context(
            "skip",
            user_data={"user_lineup": ["Zilong"]},
        )

        result = await handler(update, context)

        assert result == ConversationHandler.END
        assert "None" in agent.last_prompt

    async def test_skip_case_insensitive(self, tmp_path):
        skill_file = tmp_path / "skill.md"
        skill_file.write_text("{user_heroes} {enemy_heroes}")

        agent = FakeAgent()
        handler = suggest_heroes_enemy_team(agent, str(skill_file))

        update, context = _make_update_and_context(
            "SKIP",
            user_data={"user_lineup": ["Zilong"]},
        )

        result = await handler(update, context)

        assert result == ConversationHandler.END
        assert "None" in agent.last_prompt

    async def test_invalid_lineup_reprompts(self, tmp_path):
        skill_file = tmp_path / "skill.md"
        skill_file.write_text("{user_heroes} {enemy_heroes}")

        agent = FakeAgent()
        handler = suggest_heroes_enemy_team(agent, str(skill_file))

        update, context = _make_update_and_context(
            "A, B, C, D, E, F",
            user_data={"user_lineup": ["Zilong"]},
        )

        result = await handler(update, context)

        assert result == ENEMY_TEAM
        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "1" in reply_text and "5" in reply_text

    async def test_agent_error_sends_error_message(self, tmp_path):
        skill_file = tmp_path / "skill.md"
        skill_file.write_text("{user_heroes} {enemy_heroes}")

        class FailingAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                raise RuntimeError("agent down")

        handler = suggest_heroes_enemy_team(FailingAgent(), str(skill_file))

        update, context = _make_update_and_context(
            "Fanny",
            user_data={"user_lineup": ["Zilong"]},
        )

        result = await handler(update, context)

        assert result == ConversationHandler.END
        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "unavailable" in reply_text.lower()


class TestSuggestHeroesTimeout:
    async def test_sends_expiry_message(self):
        update, context = _make_update_and_context()

        result = await suggest_heroes_timeout(update, context)

        assert result == ConversationHandler.END
        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "expired" in reply_text.lower()


class TestBuildHandlers:
    def test_returns_conversation_handler(self, tmp_path):
        skill_file = tmp_path / "skill.md"
        skill_file.write_text("{user_heroes} {enemy_heroes}")

        agent = FakeAgent()
        commands = {
            "/suggest_heroes": {
                "skill_file": str(skill_file),
                "description": "Suggest heroes",
                "args": ["heroes"],
            }
        }

        handlers = build_handlers(agent, commands)
        assert len(handlers) == 1
        assert isinstance(handlers[0], ConversationHandler)

    def test_unknown_command_is_skipped(self):
        agent = FakeAgent()
        commands = {
            "/unknown_command": {
                "skill_file": "nonexistent.md",
                "description": "Unknown",
                "args": [],
            }
        }

        handlers = build_handlers(agent, commands)
        assert handlers == []
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_handlers.py -v`
Expected: FAIL — imports don't exist yet

**Step 3: Write the implementation**

Replace the entire `bot/handlers.py` with:

```python
# bot/handlers.py
from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from agent.base import AgentClient
from bot.skills import load_skill

logger = logging.getLogger(__name__)

HandlerFunc = Callable[
    [Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]
]

USER_TEAM = 0
ENEMY_TEAM = 1

_TIMEOUT_SECONDS = 300  # 5 minutes


def _parse_lineup(text: str) -> list[str] | None:
    heroes = [h.strip() for h in text.split(",") if h.strip()]
    if not (1 <= len(heroes) <= 5):
        return None
    return heroes


async def suggest_heroes_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.effective_message.reply_html(
        "Please enter your team lineup (1\u20135 heroes, comma-separated).\n"
        "Example: <code>Zilong, Yu Zhong, Ruby</code>"
    )
    return USER_TEAM


async def suggest_heroes_user_team(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    lineup = _parse_lineup(update.message.text)
    if lineup is None:
        await update.effective_message.reply_html(
            "Invalid lineup. Please enter 1\u20135 heroes, comma-separated."
        )
        return USER_TEAM

    context.user_data["user_lineup"] = lineup
    await update.effective_message.reply_html(
        "Got it! Now enter the enemy team lineup (1\u20135 heroes, comma-separated), "
        "or type <b>skip</b> to get suggestions based on your team only."
    )
    return ENEMY_TEAM


def suggest_heroes_enemy_team(
    agent: AgentClient, skill_path: str
) -> HandlerFunc:
    async def handler(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        text = update.message.text.strip()

        if text.lower() == "skip":
            enemy_heroes = "None"
        else:
            lineup = _parse_lineup(text)
            if lineup is None:
                await update.effective_message.reply_html(
                    "Invalid lineup. Please enter 1\u20135 heroes, comma-separated, "
                    "or type <b>skip</b>."
                )
                return ENEMY_TEAM
            enemy_heroes = ", ".join(lineup)

        user_lineup = context.user_data["user_lineup"]

        try:
            prompt = load_skill(
                skill_path,
                user_heroes=", ".join(user_lineup),
                enemy_heroes=enemy_heroes,
            )
            result = await agent.run(prompt)
            await update.effective_message.reply_html(result)
        except Exception:
            logger.exception("Agent error in /suggest_heroes")
            await update.effective_message.reply_html(
                "Sorry, the service is temporarily unavailable. "
                "Please try again later."
            )

        return ConversationHandler.END

    return handler


async def suggest_heroes_timeout(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.effective_message.reply_html(
        "Session expired. Send /suggest_heroes to start again."
    )
    return ConversationHandler.END


def build_handlers(
    agent: AgentClient, commands: dict[str, dict]
) -> list[ConversationHandler]:
    handler_builders: dict[str, Callable] = {
        "/suggest_heroes": lambda cmd_config: ConversationHandler(
            entry_points=[CommandHandler("suggest_heroes", suggest_heroes_start)],
            states={
                USER_TEAM: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        suggest_heroes_user_team,
                    ),
                ],
                ENEMY_TEAM: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        suggest_heroes_enemy_team(agent, cmd_config["skill_file"]),
                    ),
                ],
                ConversationHandler.TIMEOUT: [
                    MessageHandler(
                        filters.ALL,
                        suggest_heroes_timeout,
                    ),
                ],
            },
            fallbacks=[CommandHandler("suggest_heroes", suggest_heroes_start)],
            conversation_timeout=_TIMEOUT_SECONDS,
            per_user=True,
            per_chat=True,
        ),
    }

    handlers = []
    for cmd_name, cmd_config in commands.items():
        builder = handler_builders.get(cmd_name)
        if builder is None:
            continue
        handlers.append(builder(cmd_config))

    return handlers
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_handlers.py -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add bot/handlers.py tests/test_handlers.py
git commit -m "feat: rewrite handlers as multi-step ConversationHandler for /suggest_heroes"
```

---

### Task 4: Update bot/main.py to accept handler objects

**Files:**
- Modify: `bot/main.py:6,26-27`
- Test: `tests/test_main.py:31-58`

**Step 1: Write the failing test**

Replace `TestCreateApp` in `tests/test_main.py` with:

```python
class TestCreateApp:
    def test_creates_application_with_handlers(self):
        cfg = Config(telegram_bot_token="t")

        with (
            patch("bot.main.create_agent") as mock_create_agent,
            patch("bot.main.Application") as MockApp,
            patch("bot.main.build_handlers") as mock_build,
        ):
            mock_agent = MagicMock()
            mock_create_agent.return_value = mock_agent

            mock_builder = MagicMock()
            MockApp.builder.return_value = mock_builder
            mock_builder.token.return_value = mock_builder
            mock_builder.build.return_value = MagicMock()

            mock_handler = MagicMock()
            mock_build.return_value = [mock_handler]

            from bot.main import create_app
            app = create_app(cfg)

            MockApp.builder.assert_called_once()
            mock_builder.token.assert_called_once_with("t")
            mock_builder.build.assert_called_once()
            app.add_handler.assert_called_once_with(mock_handler)
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_main.py::TestCreateApp -v`
Expected: FAIL — `create_app` still unpacks tuples and wraps in `CommandHandler`

**Step 3: Update bot/main.py**

Replace `create_app` (lines 22-29) with:

```python
def create_app(cfg: Config) -> Application:
    agent = create_agent(cfg)
    app = Application.builder().token(cfg.telegram_bot_token).build()

    for handler in build_handlers(agent, COMMANDS):
        app.add_handler(handler)

    return app
```

Remove `CommandHandler` from the import on line 6:

```python
from telegram.ext import Application
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_main.py -v`
Expected: PASS (all 4 tests)

**Step 5: Commit**

```bash
git add bot/main.py tests/test_main.py
git commit -m "feat: update main.py to accept handler objects from build_handlers"
```

---

### Task 5: Run full test suite and verify 100% coverage

**Files:**
- No code changes expected

**Step 1: Run all tests with coverage**

Run: `python3 -m pytest --cov --cov-report=term-missing -v`
Expected: 42 tests pass (count may differ slightly), 100% coverage

**Step 2: If any tests fail or coverage < 100%, fix issues**

Common issues to check:
- Unused imports in `bot/main.py` (remove `CommandHandler` if still imported)
- Missing coverage on any new lines (add targeted test if needed)

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: resolve test/coverage issues"
```

---

### Task 6: Update doc references

**Files:**
- Modify: `docs/plans/2026-03-07-telegram-bot-server-design.md`
- Modify: `docs/plans/2026-03-07-telegram-bot-server-implementation.md`

**Step 1: Replace all team_counter/team-counter references in docs**

```bash
sed -i '' 's/team_counter/suggest_heroes/g; s/team-counter/suggest-heroes/g' \
  docs/plans/2026-03-07-telegram-bot-server-design.md \
  docs/plans/2026-03-07-telegram-bot-server-implementation.md
```

**Step 2: Verify no remaining references**

```bash
grep -r "team.counter" --include="*.py" --include="*.md" .
```

Expected: No matches (except possibly the design doc mentioning the rename itself).

**Step 3: Commit**

```bash
git add docs/
git commit -m "docs: update references from team_counter to suggest_heroes"
```

---

### Task 7: Final verification

**Step 1: Run full test suite one more time**

Run: `python3 -m pytest --cov --cov-report=term-missing -v`
Expected: All tests pass, 100% coverage

**Step 2: Verify no stale references remain**

```bash
grep -r "team.counter" --include="*.py" --include="*.md" --include="*.toml" .
```

Expected: No matches.
