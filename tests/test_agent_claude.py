# tests/test_agent_claude.py
import pytest
from unittest.mock import patch, MagicMock
from agent.claude import ClaudeAgentClient
from agent.base import AgentClient


class TestClaudeAgentClient:
    def test_is_agent_client_subclass(self):
        assert issubclass(ClaudeAgentClient, AgentClient)

    def test_init_stores_config(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mlbb_api_token="test-mlbb",
            mcp_server_module="mlbb_mcp.server",
        )
        assert client.anthropic_api_key == "test-key"
        assert client.mlbb_api_token == "test-mlbb"
        assert client.mcp_server_module == "mlbb_mcp.server"

    async def test_run_calls_query_and_returns_result(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mlbb_api_token="test-mlbb",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "Here are the counter heroes..."

        async def fake_query(*args, **kwargs):
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            result = await client.run("Suggest counters for Lancelot")

        assert result == "Here are the counter heroes..."

    async def test_run_with_system_prompt(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mlbb_api_token="test-mlbb",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "formatted response"

        captured_options = {}

        async def fake_query(*args, **kwargs):
            captured_options.update(kwargs)
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            await client.run("test", system_prompt="be concise")

        assert captured_options["options"].system_prompt == "be concise"

    async def test_run_passes_mcp_server_config(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mlbb_api_token="test-mlbb",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "response"

        captured_options = {}

        async def fake_query(*args, **kwargs):
            captured_options.update(kwargs)
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            await client.run("test")

        mcp = captured_options["options"].mcp_servers
        assert "mlbb" in mcp
        assert mcp["mlbb"]["command"] == "python"
        assert "-m" in mcp["mlbb"]["args"]
        assert "mlbb_mcp.server" in mcp["mlbb"]["args"]

    async def test_run_returns_empty_string_when_no_result(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mlbb_api_token="test-mlbb",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_other_msg = MagicMock(spec=[])  # no .result attribute

        async def fake_query(*args, **kwargs):
            yield mock_other_msg

        with patch("agent.claude.query", side_effect=fake_query):
            result = await client.run("test")

        assert result == ""

    async def test_run_sets_permission_bypass(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mlbb_api_token="test-mlbb",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "ok"
        captured_options = {}

        async def fake_query(*args, **kwargs):
            captured_options.update(kwargs)
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            await client.run("test")

        opts = captured_options["options"]
        assert opts.permission_mode == "bypassPermissions"
        assert opts.allow_dangerously_skip_permissions is True

    async def test_run_sets_env_with_api_keys(self):
        client = ClaudeAgentClient(
            anthropic_api_key="test-key",
            mlbb_api_token="test-mlbb",
            mcp_server_module="mlbb_mcp.server",
        )

        mock_result_msg = MagicMock()
        mock_result_msg.result = "ok"

        captured_options = {}

        async def fake_query(*args, **kwargs):
            captured_options.update(kwargs)
            yield mock_result_msg

        with patch("agent.claude.query", side_effect=fake_query):
            await client.run("test")

        env = captured_options["options"].env
        assert env["ANTHROPIC_API_KEY"] == "test-key"
        assert env["MLBB_API_TOKEN"] == "test-mlbb"
