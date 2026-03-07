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

        heroes = " ".join(args).replace(",", " ").strip()
        heroes = ", ".join(h.strip() for h in heroes.split() if h.strip())

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
