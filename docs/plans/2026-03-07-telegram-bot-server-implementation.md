# MLBB Telegram Bot Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python Telegram bot server that maps commands to skill prompt templates and executes them via a pluggable AI agent with MCP tools.

**Architecture:** Telegram webhook -> command handler -> load skill template -> pluggable agent (Claude Agent SDK default) -> MCP tools -> formatted response back to Telegram. Agent layer is abstract so backends can be swapped.

**Tech Stack:** Python 3.14, python-telegram-bot[webhooks], claude-agent-sdk, python-dotenv, pytest + pytest-asyncio + pytest-cov

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `bot/__init__.py`
- Create: `agent/__init__.py`
- Create: `tests/__init__.py`

**Step 1: Create `pyproject.toml`**

```toml
[project]
name = "mlbb-bot-server"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "python-telegram-bot[webhooks]>=21.0",
    "claude-agent-sdk>=0.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=6.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
source = ["bot", "agent", "config"]
omit = ["tests/*"]

[tool.coverage.report]
fail_under = 100
show_missing = true
```

**Step 2: Create `.env.example`**

```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
ANTHROPIC_API_KEY=your-anthropic-api-key
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_PORT=8443
AGENT_BACKEND=claude
```

**Step 3: Create empty `__init__.py` files**

Create empty files at:
- `bot/__init__.py`
- `agent/__init__.py`
- `tests/__init__.py`

**Step 4: Install dependencies**

Run: `pip install -e ".[dev]"`

**Step 5: Verify pytest runs**

Run: `pytest --co`
Expected: "no tests ran" (no test files yet), no import errors

**Step 6: Commit**

```bash
git add pyproject.toml .env.example bot/__init__.py agent/__init__.py tests/__init__.py
git commit -m "feat: scaffold project with dependencies and structure"
```

---

### Task 2: Config Module

**Files:**
- Create: `config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing tests**

```python
# tests/test_config.py
import os
from unittest.mock import patch


class TestLoadConfig:
    def test_loads_required_env_vars(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "TELEGRAM_BOT_TOKEN=test-token\n"
            "ANTHROPIC_API_KEY=test-key\n"
            "WEBHOOK_URL=https://example.com/webhook\n"
            "WEBHOOK_PORT=8443\n"
        )
        with patch.dict(os.environ, {}, clear=True):
            from config import load_config

            cfg = load_config(str(env_file))

        assert cfg.telegram_bot_token == "test-token"
        assert cfg.anthropic_api_key == "test-key"
        assert cfg.webhook_url == "https://example.com/webhook"
        assert cfg.webhook_port == 8443

    def test_default_webhook_port(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "TELEGRAM_BOT_TOKEN=t\n"
            "ANTHROPIC_API_KEY=k\n"
            "WEBHOOK_URL=https://example.com/webhook\n"
        )
        with patch.dict(os.environ, {}, clear=True):
            from config import load_config

            cfg = load_config(str(env_file))

        assert cfg.webhook_port == 8443

    def test_default_agent_backend(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "TELEGRAM_BOT_TOKEN=t\n"
            "ANTHROPIC_API_KEY=k\n"
            "WEBHOOK_URL=https://example.com/webhook\n"
        )
        with patch.dict(os.environ, {}, clear=True):
            from config import load_config

            cfg = load_config(str(env_file))

        assert cfg.agent_backend == "claude"

    def test_custom_agent_backend(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "TELEGRAM_BOT_TOKEN=t\n"
            "ANTHROPIC_API_KEY=k\n"
            "WEBHOOK_URL=https://example.com/webhook\n"
            "AGENT_BACKEND=openai\n"
        )
        with patch.dict(os.environ, {}, clear=True):
            from config import load_config

            cfg = load_config(str(env_file))

        assert cfg.agent_backend == "openai"

    def test_missing_required_var_raises(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TELEGRAM_BOT_TOKEN=t\n")
        import pytest

        with patch.dict(os.environ, {}, clear=True):
            from config import load_config

            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
                load_config(str(env_file))


class TestCommandRegistry:
    def test_suggest_counters_command_exists(self):
        from config import COMMANDS

        assert "/suggest_counters" in COMMANDS

    def test_suggest_counters_has_skill_file(self):
        from config import COMMANDS

        cmd = COMMANDS["/suggest_counters"]
        assert cmd["skill_file"] == "skills/suggest_counters.md"

    def test_suggest_counters_has_description(self):
        from config import COMMANDS

        cmd = COMMANDS["/suggest_counters"]
        assert "description" in cmd
        assert len(cmd["description"]) > 0

    def test_suggest_counters_has_args(self):
        from config import COMMANDS

        cmd = COMMANDS["/suggest_counters"]
        assert cmd["args"] == ["heroes"]
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `config` module does not exist

**Step 3: Write minimal implementation**

```python
# config.py
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    anthropic_api_key: str
    webhook_url: str
    webhook_port: int = 8443
    agent_backend: str = "claude"


def load_config(env_path: str = ".env") -> Config:
    load_dotenv(env_path, override=True)

    required = [
        "TELEGRAM_BOT_TOKEN", 
        "ANTHROPIC_API_KEY",
        "WEBHOOK_URL",
    ]
    for var in required:
        if not os.environ.get(var):
            raise ValueError(f"Missing required environment variable: {var}")

    return Config(
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        webhook_url=os.environ["WEBHOOK_URL"],
        webhook_port=int(os.environ.get("WEBHOOK_PORT", "8443")),
        agent_backend=os.environ.get("AGENT_BACKEND", "claude"),
    )


COMMANDS: dict[str, dict] = {
    "/suggest_counters": {
        "skill_file": "skills/suggest_counters.md",
        "description": "Suggest counter heroes for an enemy lineup",
        "args": ["heroes"],
    }
}
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v --cov=config --cov-report=term-missing`
Expected: All PASS, 100% coverage on `config.py`

**Step 5: Commit**

```bash
git add config.py tests/test_config.py
git commit -m "feat: add config module with env loading and command registry"
```

---

### Task 3: Agent Base Class

**Files:**
- Create: `agent/base.py`
- Create: `tests/test_agent_base.py`

**Step 1: Write the failing tests**

```python
# tests/test_agent_base.py
import pytest
from agent.base import AgentClient


class TestAgentClientInterface:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            AgentClient()

    def test_concrete_subclass_can_be_instantiated(self):
        class FakeAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                return "response"

        agent = FakeAgent()
        assert agent is not None

    @pytest.mark.asyncio
    async def test_concrete_subclass_run_returns_string(self):
        class FakeAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                return f"echo: {prompt}"

        agent = FakeAgent()
        result = await agent.run("hello")
        assert result == "echo: hello"

    @pytest.mark.asyncio
    async def test_concrete_subclass_run_with_system_prompt(self):
        class FakeAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                return f"sys={system_prompt} prompt={prompt}"

        agent = FakeAgent()
        result = await agent.run("hello", system_prompt="be helpful")
        assert result == "sys=be helpful prompt=hello"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_agent_base.py -v`
Expected: FAIL — `agent.base` module does not exist

**Step 3: Write minimal implementation**

```python
# agent/base.py
from __future__ import annotations

from abc import ABC, abstractmethod


class AgentClient(ABC):
    @abstractmethod
    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt to the agent and return the text response."""
        ...
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_agent_base.py -v --cov=agent.base --cov-report=term-missing`
Expected: All PASS, 100% coverage

**Step 5: Commit**

```bash
git add agent/base.py tests/test_agent_base.py
git commit -m "feat: add abstract AgentClient base class"
```

---

### Task 4: Claude Agent Implementation

**Files:**
- Create: `agent/claude.py`
- Create: `tests/test_agent_claude.py`

**Step 1: Write the failing tests**

The Claude Agent SDK spawns a CLI subprocess. We mock `query()` entirely in tests — no real API calls.

```python
# tests/test_agent_claude.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent.claude import ClaudeAgentClient
from agent.base import AgentClient


class TestClaudeAgentClient:
    def test_is_agent_client_subclass(self):
        assert issubclass(ClaudeAgentClient, AgentClient)

    def test_init_stores_config(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mcp_server_module="mlbb_mcp.server",
        )
        assert client.anthropic_api_key == "test-key"
        assert client.mcp_server_module == "mlbb_mcp.server"

    @pytest.mark.asyncio
    async def test_run_calls_query_and_returns_result(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "Here are the counter heroes..."

        async def fake_query(*args, **kwargs):
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            result = await client.run("Suggest counters for Lancelot")

        assert result == "Here are the counter heroes..."

    @pytest.mark.asyncio
    async def test_run_with_system_prompt(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "formatted response"

        captured_options = {}

        async def fake_query(*args, **kwargs):
            captured_options.update(kwargs)
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            await client.run("test", system_prompt="be concise")

        assert captured_options["options"].system_prompt == "be concise"

    @pytest.mark.asyncio
    async def test_run_passes_mcp_server_config(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "response"

        captured_options = {}

        async def fake_query(*args, **kwargs):
            captured_options.update(kwargs)
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            await client.run("test")

        mcp = captured_options["options"].mcp_servers
        assert "mlbb" in mcp
        assert mcp["mlbb"]["command"] == "python"
        assert "-m" in mcp["mlbb"]["args"]
        assert "mlbb_mcp.server" in mcp["mlbb"]["args"]

    @pytest.mark.asyncio
    async def test_run_returns_empty_string_when_no_result(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_other_msg = MagicMock(spec=[])  # no .result attribute

        async def fake_query(*args, **kwargs):
            yield mock_other_msg

        with patch("agent.claude.query", side_effect=fake_query):
            result = await client.run("test")

        assert result == ""

    @pytest.mark.asyncio
    async def test_run_sets_env_with_api_keys(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "ok"

        captured_options = {}

        async def fake_query(*args, **kwargs):
            captured_options.update(kwargs)
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            await client.run("test")

        env = captured_options["options"].env
        assert env["ANTHROPIC_API_KEY"] == "test-key"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_agent_claude.py -v`
Expected: FAIL — `agent.claude` module does not exist

**Step 3: Write minimal implementation**

```python
# agent/claude.py
from __future__ import annotations

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

from agent.base import AgentClient


class ClaudeAgentClient(AgentClient):
    def __init__(
        self,
        anthropic_api_key: str,
        mcp_server_module: str = "mlbb_mcp.server",
        model: str = "claude-haiku-4-5",
        max_turns: int = 10,
        max_budget_usd: float = 0.05,
    ) -> None:
        self.anthropic_api_key = anthropic_api_key
        self.mcp_server_module = mcp_server_module
        self.model = model
        self.max_turns = max_turns
        self.max_budget_usd = max_budget_usd

    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        options = ClaudeAgentOptions(
            model=self.model,
            max_turns=self.max_turns,
            max_budget_usd=self.max_budget_usd,
            permission_mode="bypassPermissions",
            allow_dangerously_skip_permissions=True,
            system_prompt=system_prompt,
            env={
                "ANTHROPIC_API_KEY": self.anthropic_api_key,
            },
            mcp_servers={
                "mlbb": {
                    "command": "python",
                    "args": ["-m", self.mcp_server_module],
                }
            },
        )

        result = ""
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                result = message.result

        return result
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_agent_claude.py -v --cov=agent --cov-report=term-missing`
Expected: All PASS, 100% coverage on `agent/`

**Step 5: Commit**

```bash
git add agent/claude.py tests/test_agent_claude.py
git commit -m "feat: add Claude Agent SDK implementation of AgentClient"
```

---

### Task 5: Skill Template Loading

**Files:**
- Create: `skills/suggest_counters.md`
- Create: `tests/test_skills.py`
- Create: `bot/skills.py`

**Step 1: Write the failing tests**

```python
# tests/test_skills.py
import pytest
from bot.skills import load_skill


class TestLoadSkill:
    def test_loads_and_interpolates_template(self, tmp_path):
        skill_file = tmp_path / "test_skill.md"
        skill_file.write_text("Analyze: {heroes}\nFormat as HTML.")

        result = load_skill(str(skill_file), heroes="Lancelot, Pharsa")
        assert result == "Analyze: Lancelot, Pharsa\nFormat as HTML."

    def test_no_placeholders(self, tmp_path):
        skill_file = tmp_path / "plain.md"
        skill_file.write_text("Just a plain prompt.")

        result = load_skill(str(skill_file))
        assert result == "Just a plain prompt."

    def test_multiple_placeholders(self, tmp_path):
        skill_file = tmp_path / "multi.md"
        skill_file.write_text("Heroes: {heroes}, Mode: {mode}")

        result = load_skill(str(skill_file), heroes="Tigreal", mode="ranked")
        assert result == "Heroes: Tigreal, Mode: ranked"

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            load_skill("/nonexistent/skill.md")
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_skills.py -v`
Expected: FAIL — `bot.skills` module does not exist

**Step 3: Write minimal implementation**

```python
# bot/skills.py
from __future__ import annotations

from pathlib import Path


def load_skill(skill_path: str, **kwargs: str) -> str:
    template = Path(skill_path).read_text()
    return template.format(**kwargs) if kwargs else template
```

**Step 4: Create the actual skill template**

```markdown
# skills/suggest_counters.md

Analyze the following enemy team lineup in Mobile Legends: Bang Bang and suggest the best counter heroes.

Enemy team: {heroes}

Instructions:
1. Use the get_hero_list tool to find available heroes
2. Use the get_hero_detail tool to research each enemy hero's weaknesses, counters, and the "strong_against" / "weak_against" data
3. Suggest 3-5 counter heroes with brief reasoning for each

Format your response as Telegram HTML:
- Use <b>Hero Name</b> for hero names
- Use line breaks between sections
- Structure:

<b>Counter Picks for Enemy Team</b>

<b>1. Hero Name</b> (Role)
Reason this hero counters the enemy lineup.

<b>2. Hero Name</b> (Role)
Reason this hero counters the enemy lineup.

(continue for each suggestion)

<b>Tips:</b>
- Brief team composition advice

Keep the response concise and actionable. Do not use markdown — only Telegram HTML tags.
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_skills.py -v --cov=bot.skills --cov-report=term-missing`
Expected: All PASS, 100% coverage on `bot/skills.py`

**Step 6: Commit**

```bash
git add bot/skills.py skills/suggest_counters.md tests/test_skills.py
git commit -m "feat: add skill template loading and suggest_counters skill"
```

---

### Task 6: Telegram Command Handlers

**Files:**
- Create: `bot/handlers.py`
- Create: `tests/test_handlers.py`

**Step 1: Write the failing tests**

```python
# tests/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers import suggest_counters_handler, build_handlers
from agent.base import AgentClient


def _make_update_and_context(text: str):
    """Create mock Telegram Update and Context for a command message."""
    update = MagicMock()
    update.effective_message.text = text
    update.effective_message.reply_html = AsyncMock()
    # Extract args: everything after the command
    parts = text.split(maxsplit=1)
    context = MagicMock()
    context.args = parts[1].split(",") if len(parts) > 1 else []
    # Rejoin as the raw arg string
    context.args = parts[1].strip().split(",") if len(parts) > 1 else []
    return update, context


class FakeAgent(AgentClient):
    def __init__(self, response: str = "mock response"):
        self.response = response
        self.last_prompt = None

    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        self.last_prompt = prompt
        return self.response


class TestSuggestCountersHandler:
    @pytest.mark.asyncio
    async def test_sends_agent_response_as_html(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("Counter: {heroes}")

        agent = FakeAgent(response="<b>Pick Fanny</b>")

        handler_fn = suggest_counters_handler(agent, str(skill_file))
        update, context = _make_update_and_context(
            "/suggest_counters Lancelot, Pharsa"
        )
        # Provide raw text args
        context.args = ["Lancelot,", "Pharsa"]

        await handler_fn(update, context)

        update.effective_message.reply_html.assert_called_once_with("<b>Pick Fanny</b>")

    @pytest.mark.asyncio
    async def test_passes_heroes_to_skill_template(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("Analyze: {heroes}")

        agent = FakeAgent()

        handler_fn = suggest_counters_handler(agent, str(skill_file))
        update, context = _make_update_and_context(
            "/suggest_counters Lancelot, Pharsa"
        )
        context.args = ["Lancelot,", "Pharsa"]

        await handler_fn(update, context)

        assert "Lancelot, Pharsa" in agent.last_prompt

    @pytest.mark.asyncio
    async def test_missing_args_sends_usage(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("{heroes}")

        agent = FakeAgent()

        handler_fn = suggest_counters_handler(agent, str(skill_file))
        update, context = _make_update_and_context("/suggest_counters")
        context.args = []

        await handler_fn(update, context)

        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "Usage" in reply_text or "usage" in reply_text

    @pytest.mark.asyncio
    async def test_agent_error_sends_error_message(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("{heroes}")

        class FailingAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                raise RuntimeError("agent down")

        agent = FailingAgent()

        handler_fn = suggest_counters_handler(agent, str(skill_file))
        update, context = _make_update_and_context("/suggest_counters Lancelot")
        context.args = ["Lancelot"]

        await handler_fn(update, context)

        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "unavailable" in reply_text.lower() or "error" in reply_text.lower()


class TestBuildHandlers:
    def test_returns_list_of_command_handler_tuples(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("{heroes}")

        agent = FakeAgent()
        commands = {
            "/suggest_counters": {
                "skill_file": str(skill_file),
                "description": "Suggest counters",
                "args": ["heroes"],
            }
        }

        handlers = build_handlers(agent, commands)
        assert len(handlers) == 1

        name, handler_fn = handlers[0]
        assert name == "suggest_counters"
        assert callable(handler_fn)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_handlers.py -v`
Expected: FAIL — `bot.handlers` module does not exist

**Step 3: Write minimal implementation**

```python
# bot/handlers.py
from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

from agent.base import AgentClient
from bot.skills import load_skill

logger = logging.getLogger(__name__)

HandlerFunc = Callable[
    [Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]
]


def suggest_counters_handler(
    agent: AgentClient, skill_path: str
) -> HandlerFunc:
    async def handler(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        args = context.args or []
        if not args:
            await update.effective_message.reply_html(
                "Usage: /suggest_counters Hero1, Hero2, Hero3, Hero4, Hero5"
            )
            return

        heroes = " ".join(args).replace(",", ", ").strip()
        # Normalize multiple spaces
        heroes = ", ".join(h.strip() for h in heroes.split(",") if h.strip())

        try:
            prompt = load_skill(skill_path, heroes=heroes)
            result = await agent.run(prompt)
            await update.effective_message.reply_html(result)
        except Exception:
            logger.exception("Agent error in /suggest_counters")
            await update.effective_message.reply_html(
                "Sorry, the service is temporarily unavailable. Please try again later."
            )

    return handler


def build_handlers(
    agent: AgentClient, commands: dict[str, dict]
) -> list[tuple[str, HandlerFunc]]:
    handler_map: dict[str, Callable[..., HandlerFunc]] = {
        "/suggest_counters": suggest_counters_handler,
    }

    handlers = []
    for cmd_name, cmd_config in commands.items():
        factory = handler_map.get(cmd_name)
        if factory is None:
            continue
        name = cmd_name.lstrip("/")
        handler_fn = factory(agent, cmd_config["skill_file"])
        handlers.append((name, handler_fn))

    return handlers
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_handlers.py -v --cov=bot.handlers --cov-report=term-missing`
Expected: All PASS, 100% coverage on `bot/handlers.py`

**Step 5: Commit**

```bash
git add bot/handlers.py tests/test_handlers.py
git commit -m "feat: add Telegram command handlers with skill template integration"
```

---

### Task 7: Bot Main Entry Point

**Files:**
- Create: `bot/main.py`
- Create: `tests/test_main.py`

**Step 1: Write the failing tests**

```python
# tests/test_main.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from bot.main import create_app, create_agent


class TestCreateAgent:
    def test_creates_claude_agent_for_claude_backend(self):
        from config import Config

        cfg = Config(
            telegram_bot_token="t",
            anthropic_api_key="k",
            webhook_url="https://example.com/webhook",
            agent_backend="claude",
        )

        with patch("bot.main.ClaudeAgentClient") as MockClaude:
            agent = create_agent(cfg)

        MockClaude.assert_called_once_with(
            anthropic_api_key="k",
        )

    def test_raises_for_unknown_backend(self):
        from config import Config

        cfg = Config(
            telegram_bot_token="t",
            anthropic_api_key="k",
            webhook_url="https://example.com/webhook",
            agent_backend="unknown",
        )

        with pytest.raises(ValueError, match="unknown"):
            create_agent(cfg)


class TestCreateApp:
    def test_creates_application_with_handlers(self):
        from config import Config

        cfg = Config(
            telegram_bot_token="t",
            anthropic_api_key="k",
            webhook_url="https://example.com/webhook",
        )

        with (
            patch("bot.main.create_agent") as mock_create_agent,
            patch("bot.main.Application") as MockApp,
            patch("bot.main.build_handlers") as mock_build,
            patch("bot.main.CommandHandler") as MockCmdHandler,
        ):
            mock_agent = MagicMock()
            mock_create_agent.return_value = mock_agent

            mock_builder = MagicMock()
            MockApp.builder.return_value = mock_builder
            mock_builder.token.return_value = mock_builder
            mock_builder.build.return_value = MagicMock()

            mock_handler_fn = MagicMock()
            mock_build.return_value = [("suggest_counters", mock_handler_fn)]

            app = create_app(cfg)

            MockApp.builder.assert_called_once()
            mock_builder.token.assert_called_once_with("t")
            mock_builder.build.assert_called_once()
            app.add_handler.assert_called_once()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_main.py -v`
Expected: FAIL — `bot.main` module does not exist

**Step 3: Write minimal implementation**

```python
# bot/main.py
from __future__ import annotations

import logging

from telegram.ext import Application, CommandHandler

from agent.base import AgentClient
from agent.claude import ClaudeAgentClient
from bot.handlers import build_handlers
from config import COMMANDS, Config, load_config

logger = logging.getLogger(__name__)


def create_agent(cfg: Config) -> AgentClient:
    if cfg.agent_backend == "claude":
        return ClaudeAgentClient(
            anthropic_api_key=cfg.anthropic_api_key,
        )
    raise ValueError(f"Unknown agent backend: {cfg.agent_backend}")


def create_app(cfg: Config) -> Application:
    agent = create_agent(cfg)
    app = Application.builder().token(cfg.telegram_bot_token).build()

    for name, handler_fn in build_handlers(agent, COMMANDS):
        app.add_handler(CommandHandler(name, handler_fn))

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    cfg = load_config()
    app = create_app(cfg)

    logger.info("Starting webhook on %s:%d", cfg.webhook_url, cfg.webhook_port)
    app.run_webhook(
        listen="0.0.0.0",
        port=cfg.webhook_port,
        webhook_url=cfg.webhook_url,
    )


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_main.py -v --cov=bot.main --cov-report=term-missing`
Expected: All PASS, 100% coverage on `bot/main.py`

Note: The `main()` function itself is behind `if __name__ == "__main__"` and calls `run_webhook` which blocks. We test `create_agent` and `create_app` which contain the logic. If coverage is not 100%, add a test for `main()` that mocks `load_config`, `create_app`, and `app.run_webhook`.

**Step 5: If `main()` needs coverage, add this test:**

```python
class TestMain:
    def test_main_starts_webhook(self):
        from config import Config

        mock_cfg = Config(
            telegram_bot_token="t",
            anthropic_api_key="k",
            webhook_url="https://example.com/webhook",
            webhook_port=9999,
        )

        with (
            patch("bot.main.load_config", return_value=mock_cfg),
            patch("bot.main.create_app") as mock_create_app,
        ):
            mock_app = MagicMock()
            mock_create_app.return_value = mock_app

            from bot.main import main

            main()

            mock_app.run_webhook.assert_called_once_with(
                listen="0.0.0.0",
                port=9999,
                webhook_url="https://example.com/webhook",
            )
```

**Step 6: Run full coverage check**

Run: `pytest tests/test_main.py -v --cov=bot.main --cov-report=term-missing`
Expected: All PASS, 100% coverage

**Step 7: Commit**

```bash
git add bot/main.py tests/test_main.py
git commit -m "feat: add bot entry point with webhook setup"
```

---

### Task 8: Full Coverage Verification & Cleanup

**Files:**
- Modify: `pyproject.toml` (if needed)

**Step 1: Run full test suite with coverage**

Run: `pytest --cov=bot --cov=agent --cov=config --cov-report=term-missing --cov-fail-under=100 -v`
Expected: All PASS, 100% coverage across all modules

**Step 2: If any lines are uncovered, write targeted tests**

Check the "Missing" column in coverage output. Add tests for any uncovered branches.

**Step 3: Run final verification**

Run: `pytest --cov=bot --cov=agent --cov=config --cov-report=term-missing --cov-fail-under=100 -v`
Expected: All PASS, 100% coverage, no missing lines

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: ensure 100% test coverage"
```

---

### Task 9: Documentation & Final Commit

**Files:**
- Verify: `.env.example` is up to date
- Verify: `skills/suggest_counters.md` exists

**Step 1: Verify `.env.example` has all required variables**

Run: `cat .env.example`
Expected: Contains all 6 env vars from design doc

**Step 2: Verify skill template exists**

Run: `cat skills/suggest_counters.md`
Expected: Contains the prompt template with `{heroes}` placeholder

**Step 3: Final full test run**

Run: `pytest --cov=bot --cov=agent --cov=config --cov-report=term-missing --cov-fail-under=100 -v`
Expected: All PASS, 100% coverage

**Step 4: Commit any remaining files**

```bash
git add -A
git commit -m "chore: finalize project structure and documentation"
```

---

## Execution Notes

- Tasks 1-5 are independent foundations and could be parallelized
- Tasks 6-7 depend on Tasks 2-5 (handlers need agent, skills, config)
- Task 8 is a verification pass
- Task 9 is cleanup

**Key testing principle:** The agent layer is always mocked in handler/main tests. Only `tests/test_agent_claude.py` tests the Claude implementation, and it mocks the `query()` function. No real API calls are made in any test.
