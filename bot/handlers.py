# bot/handlers.py
from __future__ import annotations

import logging
import re
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

_USAGE = (
    "Usage: <code>/team_counter &lt;user_team&gt; VS &lt;enemy_team&gt;</code>\n"
    "Each lineup: 1\u20135 heroes, comma-separated.\n"
    "Example: <code>/team_counter Zilong, Yu Zhong VS Fanny, Lancelot</code>"
)

_VS_RE = re.compile(r"\bvs\b", re.IGNORECASE)


def team_counter_handler(
    agent: AgentClient, skill_path: str
) -> HandlerFunc:
    async def handler(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        args = context.args or []
        if not args:
            await update.effective_message.reply_html(_USAGE)
            return

        raw = " ".join(args)
        parts = _VS_RE.split(raw)

        if len(parts) != 2:
            await update.effective_message.reply_html(
                "Invalid format: provide exactly two lineups separated by <code>VS</code>.\n\n"
                + _USAGE
            )
            return

        user_lineup = [h.strip() for h in parts[0].split(",") if h.strip()]
        enemy_lineup = [h.strip() for h in parts[1].split(",") if h.strip()]

        errors: list[str] = []
        if not (1 <= len(user_lineup) <= 5):
            errors.append(f"User team must have 1\u20135 heroes (got {len(user_lineup)})")
        if not (1 <= len(enemy_lineup) <= 5):
            errors.append(f"Enemy team must have 1\u20135 heroes (got {len(enemy_lineup)})")

        if errors:
            await update.effective_message.reply_html(
                "\n".join(f"\u2022 {e}" for e in errors) + "\n\n" + _USAGE
            )
            return

        try:
            prompt = load_skill(
                skill_path,
                user_heroes=", ".join(user_lineup),
                enemy_heroes=", ".join(enemy_lineup),
            )
            result = await agent.run(prompt)
            await update.effective_message.reply_html(result)
        except Exception:
            logger.exception("Agent error in /team_counter")
            await update.effective_message.reply_html(
                "Sorry, the service is temporarily unavailable. Please try again later."
            )

    return handler


def build_handlers(
    agent: AgentClient, commands: dict[str, dict]
) -> list[tuple[str, HandlerFunc]]:
    handler_map: dict[str, Callable[..., HandlerFunc]] = {
        "/team_counter": team_counter_handler,
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
