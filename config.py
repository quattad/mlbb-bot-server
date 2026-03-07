# config.py
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    anthropic_api_key: str
    mlbb_api_token: str
    webhook_url: str
    webhook_port: int = 8443
    agent_backend: str = "claude"


def load_config(env_path: str = ".env") -> Config:
    load_dotenv(env_path, override=True)

    required = ["TELEGRAM_BOT_TOKEN", "ANTHROPIC_API_KEY", "MLBB_API_TOKEN", "WEBHOOK_URL"]
    for var in required:
        if var not in os.environ:
            raise ValueError(f"Missing required environment variable: {var}")
        if not os.environ[var].strip():
            raise ValueError(f"Environment variable {var} is set but empty")

    port_str = os.environ.get("WEBHOOK_PORT", "8443")
    try:
        webhook_port_val = int(port_str)
    except ValueError:
        raise ValueError(f"WEBHOOK_PORT must be an integer, got: {port_str!r}")

    return Config(
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        mlbb_api_token=os.environ["MLBB_API_TOKEN"],
        webhook_url=os.environ["WEBHOOK_URL"],
        webhook_port=webhook_port_val,
        agent_backend=os.environ.get("AGENT_BACKEND", "claude"),
    )


COMMANDS: dict[str, dict] = {
    "/suggest_counters": {
        "skill_file": "skills/suggest_counters.md",
        "description": "Suggest counter heroes for an enemy lineup",
        "args": ["heroes"],
    }
}
