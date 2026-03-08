# agent/claude.py
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from agent.base import AgentClient

_SKILLS_DIR = Path(__file__).parent.parent / "skills"

logger = logging.getLogger(__name__)


class ClaudeAgentClient(AgentClient):
    def __init__(
        self,
        mcp_server_module: str = "mlbb_mcp.server",
        model: str = "claude-haiku-4-5",
    ) -> None:
        self.mcp_server_module = mcp_server_module
        self.model = model

    async def run(self, prompt: str, system_prompt: str | None = None) -> str:
        mcp_config = {
            "mcpServers": {
                "mlbb": {
                    "command": "python3",
                    "args": ["-m", self.mcp_server_module],
                }
            }
        }

        cmd = [
            "claude", "--print",
            "--output-format", "text",
            "--model", self.model,
            "--dangerously-skip-permissions",
            "--add-dir", str(_SKILLS_DIR),
            "--mcp-config", json.dumps(mcp_config),
        ]
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])
        cmd.extend(["--", prompt])

        logger.info("command sent to claude: %s", cmd)

        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await proc.communicate()
        result = stdout.decode().strip()
        logger.info("Claude response: %s", result)
        if stderr:
            logger.debug("Claude stderr: %s", stderr.decode().strip())
        return result
