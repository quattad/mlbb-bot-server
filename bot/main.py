# bot/main.py
from __future__ import annotations

import logging

from telegram.ext import Application

from agent.base import AgentClient
from agent.claude import ClaudeAgentClient
from bot.handlers import build_handlers
from config import COMMANDS, Config, load_config

logger = logging.getLogger(__name__)


def create_agent(cfg: Config) -> AgentClient:
    if cfg.agent_backend == "claude":
        return ClaudeAgentClient()
    raise ValueError(f"Unknown agent backend: {cfg.agent_backend}")


def create_app(cfg: Config) -> Application:
    agent = create_agent(cfg)
    app = Application.builder().token(cfg.telegram_bot_token).build()

    for handler in build_handlers(agent, COMMANDS):
        app.add_handler(handler)

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    cfg = load_config()
    app = create_app(cfg)

    logger.info("Starting polling")
    app.run_polling()


if __name__ == "__main__":  # pragma: no cover
    main()
