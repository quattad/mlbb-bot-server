# tests/test_agent_claude.py
import json
import pytest
from unittest.mock import patch, AsyncMock
from agent.claude import ClaudeAgentClient
from agent.base import AgentClient


class TestClaudeAgentClient:
    def test_is_agent_client_subclass(self):
        assert issubclass(ClaudeAgentClient, AgentClient)

    def test_init_stores_config(self):
        client = ClaudeAgentClient(mcp_server_module="mlbb_mcp.server")
        assert client.mcp_server_module == "mlbb_mcp.server"

    async def test_run_calls_claude_and_returns_stdout(self):
        client = ClaudeAgentClient(mcp_server_module="mlbb_mcp.server")

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"Here are the counter heroes...", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            result = await client.run("Suggest counters for Lancelot")

        assert result == "Here are the counter heroes..."
        mock_exec.assert_called_once()

    async def test_run_passes_prompt_as_last_arg(self):
        client = ClaudeAgentClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"response", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            await client.run("my prompt")

        args = mock_exec.call_args[0]
        assert args[-1] == "my prompt"

    async def test_run_includes_system_prompt_flag(self):
        client = ClaudeAgentClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"response", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            await client.run("test", system_prompt="be concise")

        args = mock_exec.call_args[0]
        assert "--system-prompt" in args
        assert "be concise" in args

    async def test_run_passes_mcp_config_with_python3(self):
        client = ClaudeAgentClient(mcp_server_module="mlbb_mcp.server")

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"response", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            await client.run("test")

        args = mock_exec.call_args[0]
        mcp_idx = list(args).index("--mcp-config")
        mcp_config = json.loads(args[mcp_idx + 1])
        assert "mlbb" in mcp_config["mcpServers"]
        assert mcp_config["mcpServers"]["mlbb"]["command"] == "python3"
        assert "-m" in mcp_config["mcpServers"]["mlbb"]["args"]
        assert "mlbb_mcp.server" in mcp_config["mcpServers"]["mlbb"]["args"]

    async def test_run_returns_empty_string_when_no_output(self):
        client = ClaudeAgentClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await client.run("test")

        assert result == ""

    async def test_run_strips_claudecode_from_env(self):
        client = ClaudeAgentClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"ok", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            with patch.dict("os.environ", {"CLAUDECODE": "1"}):
                await client.run("test")

        kwargs = mock_exec.call_args[1]
        assert "CLAUDECODE" not in kwargs["env"]

    async def test_run_uses_dangerously_skip_permissions(self):
        client = ClaudeAgentClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"ok", b"")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
            await client.run("test")

        args = mock_exec.call_args[0]
        assert "--dangerously-skip-permissions" in args

    async def test_run_logs_stderr_when_present(self):
        client = ClaudeAgentClient()

        mock_proc = AsyncMock()
        mock_proc.communicate.return_value = (b"ok", b"some warning")

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await client.run("test")

        assert result == "ok"
