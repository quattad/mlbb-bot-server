# agent/base.py
from __future__ import annotations

from abc import ABC, abstractmethod


class AgentClient(ABC):
    @abstractmethod
    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        """Send a prompt to the agent and return the text response."""
        ...  # pragma: no cover
