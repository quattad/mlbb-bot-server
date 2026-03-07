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
            mlbb_api_token=cfg.mlbb_api_token,
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


if __name__ == "__main__":  # pragma: no cover
    main()
