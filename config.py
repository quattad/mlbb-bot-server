# config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).parent


@dataclass(frozen=True)
class Config:
    telegram_bot_token: str
    agent_backend: str = "claude"


def load_config(env_path: str = ".env") -> Config:
    load_dotenv(env_path, override=True)

    required = ["TELEGRAM_BOT_TOKEN"]
    for var in required:
        if var not in os.environ:
            raise ValueError(f"Missing required environment variable: {var}")
        if not os.environ[var].strip():
            raise ValueError(f"Environment variable {var} is set but empty")

    return Config(
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        agent_backend=os.environ.get("AGENT_BACKEND", "claude"),
    )


COMMANDS: dict[str, dict] = {
    "/suggest_counters": {
        "skill_file": str(_PROJECT_ROOT / "skills" / "suggest_counters.md"),
        "description": "Suggest counter heroes for an enemy lineup",
        "args": ["heroes"],
    }
}
