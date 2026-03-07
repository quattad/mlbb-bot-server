# bot/skills.py
from __future__ import annotations

from pathlib import Path


def load_skill(skill_path: str, **kwargs: str) -> str:
    template = Path(skill_path).read_text()
    return template.format(**kwargs) if kwargs else template
