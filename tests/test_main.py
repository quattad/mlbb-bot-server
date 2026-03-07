# tests/test_main.py
import pytest
from unittest.mock import patch, MagicMock
from config import Config


class TestCreateAgent:
    def test_creates_claude_agent_for_claude_backend(self):
        cfg = Config(
            telegram_bot_token="t",
            anthropic_api_key="k",
            mlbb_api_token="m",
            webhook_url="https://example.com/webhook",
            agent_backend="claude",
        )

        with patch("bot.main.ClaudeAgentClient") as MockClaude:
            from bot.main import create_agent
            agent = create_agent(cfg)

        MockClaude.assert_called_once_with(
            anthropic_api_key="k",
            mlbb_api_token="m",
        )

    def test_raises_for_unknown_backend(self):
        cfg = Config(
            telegram_bot_token="t",
            anthropic_api_key="k",
            mlbb_api_token="m",
            webhook_url="https://example.com/webhook",
            agent_backend="unknown",
        )

        from bot.main import create_agent
        with pytest.raises(ValueError, match="unknown"):
            create_agent(cfg)


class TestCreateApp:
    def test_creates_application_with_handlers(self):
        cfg = Config(
            telegram_bot_token="t",
            anthropic_api_key="k",
            mlbb_api_token="m",
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

            from bot.main import create_app
            app = create_app(cfg)

            MockApp.builder.assert_called_once()
            mock_builder.token.assert_called_once_with("t")
            mock_builder.build.assert_called_once()
            app.add_handler.assert_called_once()


class TestMain:
    def test_main_starts_webhook(self):
        mock_cfg = Config(
            telegram_bot_token="t",
            anthropic_api_key="k",
            mlbb_api_token="m",
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
