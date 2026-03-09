# bot/handlers.py
from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from agent.base import AgentClient
from bot.skills import load_skill

logger = logging.getLogger(__name__)

HandlerFunc = Callable[
    [Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]
]

USER_TEAM = 0
ENEMY_TEAM = 1

_TIMEOUT_SECONDS = 300  # 5 minutes


def _parse_lineup(text: str) -> list[str] | None:
    heroes = [h.strip() for h in text.split(",") if h.strip()]
    if not (1 <= len(heroes) <= 5):
        return None
    return heroes


async def suggest_heroes_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.effective_message.reply_html(
        "Please enter your team lineup (1\u20135 heroes, comma-separated).\n"
        "Example: <code>Zilong, Yu Zhong, Ruby</code>"
    )
    return USER_TEAM


async def suggest_heroes_user_team(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    lineup = _parse_lineup(update.message.text)
    if lineup is None:
        await update.effective_message.reply_html(
            "Invalid lineup. Please enter 1\u20135 heroes, comma-separated."
        )
        return USER_TEAM

    context.user_data["user_lineup"] = lineup
    await update.effective_message.reply_html(
        "Got it! Now enter the enemy team lineup (1\u20135 heroes, comma-separated), "
        "or type <b>skip</b> to get suggestions based on your team only."
    )
    return ENEMY_TEAM


def suggest_heroes_enemy_team(
    agent: AgentClient, skill_path: str
) -> HandlerFunc:
    async def handler(
        update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        text = update.message.text.strip()

        if text.lower() == "skip":
            enemy_heroes = "None"
        else:
            lineup = _parse_lineup(text)
            if lineup is None:
                await update.effective_message.reply_html(
                    "Invalid lineup. Please enter 1\u20135 heroes, comma-separated, "
                    "or type <b>skip</b>."
                )
                return ENEMY_TEAM
            enemy_heroes = ", ".join(lineup)

        user_lineup = context.user_data["user_lineup"]

        await update.effective_message.reply_html("Generating suggestions...")

        try:
            prompt = load_skill(
                skill_path,
                user_heroes=", ".join(user_lineup),
                enemy_heroes=enemy_heroes,
            )
            result = await agent.run(prompt)
            await update.effective_message.reply_html(result)
        except Exception:
            logger.exception("Agent error in /suggest_heroes")
            await update.effective_message.reply_html(
                "Sorry, the service is temporarily unavailable. "
                "Please try again later."
            )

        return ConversationHandler.END

    return handler


async def suggest_heroes_timeout(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    await update.effective_message.reply_html(
        "Session expired. Send /suggest_heroes to start again."
    )
    return ConversationHandler.END


def build_handlers(
    agent: AgentClient, commands: dict[str, dict]
) -> list[ConversationHandler]:
    handler_builders: dict[str, Callable] = {
        "/suggest_heroes": lambda cmd_config: ConversationHandler(
            entry_points=[CommandHandler("suggest_heroes", suggest_heroes_start)],
            states={
                USER_TEAM: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        suggest_heroes_user_team,
                    ),
                ],
                ENEMY_TEAM: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        suggest_heroes_enemy_team(agent, cmd_config["skill_file"]),
                    ),
                ],
                ConversationHandler.TIMEOUT: [
                    MessageHandler(
                        filters.ALL,
                        suggest_heroes_timeout,
                    ),
                ],
            },
            fallbacks=[CommandHandler("suggest_heroes", suggest_heroes_start)],
            conversation_timeout=_TIMEOUT_SECONDS,
            per_user=True,
            per_chat=True,
        ),
    }

    handlers = []
    for cmd_name, cmd_config in commands.items():
        builder = handler_builders.get(cmd_name)
        if builder is None:
            continue
        handlers.append(builder(cmd_config))

    return handlers
