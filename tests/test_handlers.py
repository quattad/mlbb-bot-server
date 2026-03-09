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
