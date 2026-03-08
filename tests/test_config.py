# tests/test_config.py
import os
import pytest
from unittest.mock import patch
from config import load_config, COMMANDS


class TestLoadConfig:
    def test_loads_required_env_vars(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TELEGRAM_BOT_TOKEN=test-token\n")
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config(str(env_file))

        assert cfg.telegram_bot_token == "test-token"

    def test_default_agent_backend(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TELEGRAM_BOT_TOKEN=t\n")
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config(str(env_file))

        assert cfg.agent_backend == "claude"

    def test_custom_agent_backend(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "TELEGRAM_BOT_TOKEN=t\n"
            "AGENT_BACKEND=openai\n"
        )
        with patch.dict(os.environ, {}, clear=True):
            cfg = load_config(str(env_file))

        assert cfg.agent_backend == "openai"

    def test_missing_required_var_raises(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("")
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN"):
                load_config(str(env_file))

    def test_empty_required_var_raises(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TELEGRAM_BOT_TOKEN=   \n")
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="set but empty"):
                load_config(str(env_file))


class TestCommandRegistry:
    def test_team_counter_command_exists(self):
        assert "/team_counter" in COMMANDS

    def test_team_counter_has_skill_file(self):
        cmd = COMMANDS["/team_counter"]
        assert cmd["skill_file"].endswith("skills/team-counter/SKILL.md")

    def test_team_counter_has_description(self):
        cmd = COMMANDS["/team_counter"]
        assert "description" in cmd
        assert len(cmd["description"]) > 0

    def test_team_counter_has_args(self):
        cmd = COMMANDS["/team_counter"]
        assert cmd["args"] == ["heroes"]
