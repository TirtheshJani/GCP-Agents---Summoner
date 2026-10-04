"""Tests for the base agent framework."""

from __future__ import annotations

from typing import Any

import pytest

from agents.base_agent import AgentState, BaseAgent, MemoryStore, TaskResult

# ---------------------------------------------------------------------------
# Concrete test agent
# ---------------------------------------------------------------------------


class EchoAgent(BaseAgent):
    """Trivial agent that echoes its input (for testing)."""

    @property
    def name(self) -> str:
        return "echo"

    def plan(self, task: str) -> str:
        return f"echo: {task}"

    def execute(self, plan: str) -> Any:
        return plan.upper()


class FailingAgent(BaseAgent):
    """Agent whose execute always raises."""

    @property
    def name(self) -> str:
        return "fail"

    def plan(self, task: str) -> str:
        return task

    def execute(self, plan: str) -> Any:
        raise RuntimeError("deliberate failure")


class RejectingAgent(BaseAgent):
    """Agent whose reflect always returns False."""

    @property
    def name(self) -> str:
        return "reject"

    def plan(self, task: str) -> str:
        return task

    def execute(self, plan: str) -> Any:
        return "some output"

    def reflect(self, task: str, result: Any) -> bool:
        return False


# ---------------------------------------------------------------------------
# Tests - BaseAgent lifecycle
# ---------------------------------------------------------------------------


class TestBaseAgent:
    def test_successful_run(self):
        agent = EchoAgent()
        result = agent.run("hello world")

        assert result.success is True
        assert result.output == "ECHO: HELLO WORLD"
        assert result.agent_id.startswith("echo-")
        assert result.duration_seconds > 0
        assert agent.state == AgentState.COMPLETED

    def test_agent_id_format(self):
        agent = EchoAgent()
        assert agent.agent_id.startswith("echo-")
        assert len(agent.agent_id) == len("echo-") + 8

    def test_initial_state_is_idle(self):
        agent = EchoAgent()
        assert agent.state == AgentState.IDLE

    def test_failing_agent_raises(self):
        agent = FailingAgent()
        with pytest.raises(RuntimeError, match="deliberate failure"):
            agent.run("anything")
        assert agent.state == AgentState.FAILED

    def test_rejecting_agent_returns_failure(self):
        agent = RejectingAgent()
        # RejectingAgent.reflect returns False, but the retry decorator
        # will re-attempt 3 times. All attempts will fail reflection,
        # but since no exception is raised, the last result is returned.
        result = agent.run("anything")
        assert result.success is False
        assert result.error == "Reflection rejected the result"

    def test_repr(self):
        agent = EchoAgent()
        r = repr(agent)
        assert "EchoAgent" in r
        assert "idle" in r


# ---------------------------------------------------------------------------
# Tests - TaskResult
# ---------------------------------------------------------------------------


class TestTaskResult:
    def test_success_summary(self):
        r = TaskResult(
            task_id="abc123",
            agent_id="echo-12345678",
            success=True,
            output="done",
            duration_seconds=1.5,
        )
        s = r.summary()
        assert "[SUCCESS]" in s
        assert "abc123" in s

    def test_failure_summary(self):
        r = TaskResult(
            task_id="def456",
            agent_id="fail-87654321",
            success=False,
            error="boom",
            duration_seconds=0.1,
        )
        s = r.summary()
        assert "[FAILED]" in s


# ---------------------------------------------------------------------------
# Tests - MemoryStore
# ---------------------------------------------------------------------------


class TestMemoryStore:
    def test_set_get(self):
        store = MemoryStore()
        store.set("key", "value")
        assert store.get("key") == "value"

    def test_get_default(self):
        store = MemoryStore()
        assert store.get("missing", "default") == "default"

    def test_delete(self):
        store = MemoryStore()
        store.set("key", "value")
        store.delete("key")
        assert store.get("key") is None

    def test_list_keys(self):
        store = MemoryStore()
        store.set("a", 1)
        store.set("b", 2)
        assert sorted(store.list_keys()) == ["a", "b"]

    def test_clear(self):
        store = MemoryStore()
        store.set("a", 1)
        store.clear()
        assert store.list_keys() == []
