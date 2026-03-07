# tests/test_config.py
import os
from unittest.mock import patch


class TestLoadConfig:
    def test_loads_required_env_vars(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "TELEGRAM_BOT_TOKEN=test-token\n"
            "ANTHROPIC_API_KEY=test-key\n"
            "MLBB_API_TOKEN=test-mlbb\n"
            "WEBHOOK_URL=https://example.com/webhook\n"
            "WEBHOOK_PORT=8443\n"
        )
        with patch.dict(os.environ, {}, clear=True):
            from config import load_config

            cfg = load_config(str(env_file))

        assert cfg.telegram_bot_token == "test-token"
        assert cfg.anthropic_api_key == "test-key"
        assert cfg.mlbb_api_token == "test-mlbb"
        assert cfg.webhook_url == "https://example.com/webhook"
        assert cfg.webhook_port == 8443

    def test_default_webhook_port(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "TELEGRAM_BOT_TOKEN=t\n"
            "ANTHROPIC_API_KEY=k\n"
            "MLBB_API_TOKEN=m\n"
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
            "MLBB_API_TOKEN=m\n"
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
            "MLBB_API_TOKEN=m\n"
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
