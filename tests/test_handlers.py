# tests/test_handlers.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.handlers import suggest_counters_handler, build_handlers
from agent.base import AgentClient


def _make_update_and_context(args: list[str]):
    """Create mock Telegram Update and Context."""
    update = MagicMock()
    update.effective_message.reply_html = AsyncMock()
    context = MagicMock()
    context.args = args
    return update, context


class FakeAgent(AgentClient):
    def __init__(self, response: str = "mock response"):
        self.response = response
        self.last_prompt = None

    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        self.last_prompt = prompt
        return self.response


class TestSuggestCountersHandler:
    async def test_sends_agent_response_as_html(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("Counter: {heroes}")

        agent = FakeAgent(response="<b>Pick Fanny</b>")
        handler_fn = suggest_counters_handler(agent, str(skill_file))
        update, context = _make_update_and_context(["Lancelot,", "Pharsa"])

        await handler_fn(update, context)

        update.effective_message.reply_html.assert_called_once_with("<b>Pick Fanny</b>")

    async def test_passes_heroes_to_skill_template(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("Analyze: {heroes}")

        agent = FakeAgent()
        handler_fn = suggest_counters_handler(agent, str(skill_file))
        update, context = _make_update_and_context(["Lancelot,", "Pharsa"])

        await handler_fn(update, context)

        assert "Lancelot" in agent.last_prompt
        assert "Pharsa" in agent.last_prompt

    async def test_missing_args_sends_usage(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("{heroes}")

        agent = FakeAgent()
        handler_fn = suggest_counters_handler(agent, str(skill_file))
        update, context = _make_update_and_context([])

        await handler_fn(update, context)

        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "usage" in reply_text.lower()

    async def test_multi_word_hero_names_are_preserved(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("Analyze: {heroes}")

        agent = FakeAgent()
        handler_fn = suggest_counters_handler(agent, str(skill_file))
        # Args as Telegram would parse "/suggest_counters Sun Wukong, Lancelot"
        update, context = _make_update_and_context(["Sun", "Wukong,", "Lancelot"])

        await handler_fn(update, context)

        assert "Sun Wukong" in agent.last_prompt
        assert "Lancelot" in agent.last_prompt

    async def test_agent_error_sends_error_message(self, tmp_path):
        skill_file = tmp_path / "suggest_counters.md"
        skill_file.write_text("{heroes}")

        class FailingAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                raise RuntimeError("agent down")

        agent = FailingAgent()
        handler_fn = suggest_counters_handler(agent, str(skill_file))
        update, context = _make_update_and_context(["Lancelot"])

        await handler_fn(update, context)

        reply_text = update.effective_message.reply_html.call_args[0][0]
        assert "unavailable" in reply_text.lower()


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

    def test_unknown_command_is_skipped(self, tmp_path):
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
