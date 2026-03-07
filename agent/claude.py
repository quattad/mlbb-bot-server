# agent/claude.py
from __future__ import annotations

try:
    from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage  # pragma: no cover
except ImportError:
    # Stub definitions for when claude-agent-sdk is not installed.
    # In production, install claude-agent-sdk.
    from dataclasses import dataclass, field
    from typing import Any

    @dataclass
    class ClaudeAgentOptions:
        model: str = ""
        max_turns: int = 10
        max_budget_usd: float = 0.05
        permission_mode: str = "default"
        allow_dangerously_skip_permissions: bool = False
        system_prompt: str | None = None
        env: dict[str, str] = field(default_factory=dict)
        mcp_servers: dict[str, Any] = field(default_factory=dict)

    @dataclass
    class ResultMessage:
        result: str

    async def query(prompt: str, options: ClaudeAgentOptions):  # pragma: no cover
        raise NotImplementedError("claude-agent-sdk is not installed")
        yield  # make it an async generator

from agent.base import AgentClient


class ClaudeAgentClient(AgentClient):
    def __init__(
        self,
        anthropic_api_key: str,
        mlbb_api_token: str,
        mcp_server_module: str = "mlbb_mcp.server",
        model: str = "claude-haiku-4-5",
        max_turns: int = 10,
        max_budget_usd: float = 0.05,
    ) -> None:
        self.anthropic_api_key = anthropic_api_key
        self.mlbb_api_token = mlbb_api_token
        self.mcp_server_module = mcp_server_module
        self.model = model
        self.max_turns = max_turns
        self.max_budget_usd = max_budget_usd

    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        options = ClaudeAgentOptions(
            model=self.model,
            max_turns=self.max_turns,
            max_budget_usd=self.max_budget_usd,
            permission_mode="bypassPermissions",
            allow_dangerously_skip_permissions=True,
            system_prompt=system_prompt,
            env={
                "ANTHROPIC_API_KEY": self.anthropic_api_key,
                "MLBB_API_TOKEN": self.mlbb_api_token,
            },
            mcp_servers={
                "mlbb": {
                    "command": "python",
                    "args": ["-m", self.mcp_server_module],
                }
            },
        )

        result = ""
        async for message in query(prompt=prompt, options=options):
            if hasattr(message, "result"):
                result = message.result
        return result
