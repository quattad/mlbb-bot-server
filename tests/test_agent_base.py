# tests/test_agent_base.py
import pytest
from agent.base import AgentClient


class TestAgentClientInterface:
    def test_cannot_instantiate_abstract_class(self):
        with pytest.raises(TypeError):
            AgentClient()

    def test_concrete_subclass_can_be_instantiated(self):
        class FakeAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                return "response"

        agent = FakeAgent()
        assert agent is not None

    async def test_concrete_subclass_run_returns_string(self):
        class FakeAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                return f"echo: {prompt}"

        agent = FakeAgent()
        result = await agent.run("hello")
        assert result == "echo: hello"

    async def test_concrete_subclass_run_with_system_prompt(self):
        class FakeAgent(AgentClient):
            async def run(self, prompt: str, system_prompt: str | None = None) -> str:
                return f"sys={system_prompt} prompt={prompt}"

        agent = FakeAgent()
        result = await agent.run("hello", system_prompt="be helpful")
        assert result == "sys=be helpful prompt=hello"
