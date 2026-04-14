"""Base agent framework for GCP Agents - Summoner.

Provides the abstract :class:`BaseAgent` that every specialised agent extends.
An agent follows a simple lifecycle:

    1. ``plan``   - decide *what* to do given a task description.
    2. ``execute`` - carry out the plan (call tools, APIs, models).
    3. ``reflect`` - review the result and decide if the task is complete.

The base class wires up structured logging, retry logic, and an in-memory
or Firestore-backed memory store so subclasses can focus on domain logic.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from config import Settings, load_config

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class AgentState(str, Enum):
    """Lifecycle states of an agent."""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskResult:
    """Container for the output of a single task execution."""

    task_id: str
    agent_id: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{status}] task={self.task_id} agent={self.agent_id} ({self.duration_seconds:.2f}s)"


# ---------------------------------------------------------------------------
# Memory store
# ---------------------------------------------------------------------------

class MemoryStore:
    """Simple in-memory key/value store for agent state.

    Can be swapped for a Firestore-backed implementation via
    :class:`FirestoreMemoryStore`.
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def list_keys(self) -> list[str]:
        return list(self._store.keys())

    def clear(self) -> None:
        self._store.clear()


# ---------------------------------------------------------------------------
# Base agent
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """Abstract base class for all agents.

    Subclasses must implement :meth:`plan`, :meth:`execute`, and optionally
    override :meth:`reflect`.

    Example usage::

        class GreeterAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "greeter"

            def plan(self, task: str) -> str:
                return f"Say hello for: {task}"

            def execute(self, plan: str) -> Any:
                return f"Hello! You asked me to: {plan}"

        agent = GreeterAgent()
        result = agent.run("greet the user")
        print(result.output)  # "Hello! You asked me to: Say hello for: greet the user"
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.agent_id: str = f"{self.name}-{uuid.uuid4().hex[:8]}"
        self.settings: Settings = settings or load_config()
        self.state: AgentState = AgentState.IDLE
        self.memory: MemoryStore = MemoryStore()
        self._log = logger.bind(agent_id=self.agent_id, agent_name=self.name)

    # -- Abstract interface --------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name (e.g. ``"research"``)."""

    @abstractmethod
    def plan(self, task: str) -> str:
        """Decide how to approach *task*. Return a plan string."""

    @abstractmethod
    def execute(self, plan: str) -> Any:
        """Carry out *plan* and return a raw result."""

    # -- Optional overrides --------------------------------------------------

    def reflect(self, task: str, result: Any) -> bool:
        """Return ``True`` if the result satisfactorily addresses *task*.

        The default implementation always returns ``True``.  Override for
        self-critique / retry behaviour.
        """
        return True

    # -- Public API ----------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def run(self, task: str) -> TaskResult:
        """Run the full plan-execute-reflect cycle for *task*.

        Returns:
            :class:`TaskResult` with the outcome.
        """
        task_id = uuid.uuid4().hex[:12]
        start = time.monotonic()
        self._log.info("task.start", task_id=task_id, task=task)

        try:
            # 1. Plan
            self._set_state(AgentState.PLANNING)
            plan = self.plan(task)
            self._log.info("task.planned", task_id=task_id, plan=plan)

            # 2. Execute
            self._set_state(AgentState.EXECUTING)
            raw_result = self.execute(plan)
            self._log.info("task.executed", task_id=task_id)

            # 3. Reflect
            self._set_state(AgentState.REFLECTING)
            ok = self.reflect(task, raw_result)

            if ok:
                self._set_state(AgentState.COMPLETED)
                result = TaskResult(
                    task_id=task_id,
                    agent_id=self.agent_id,
                    success=True,
                    output=raw_result,
                    duration_seconds=time.monotonic() - start,
                )
            else:
                self._set_state(AgentState.FAILED)
                result = TaskResult(
                    task_id=task_id,
                    agent_id=self.agent_id,
                    success=False,
                    error="Reflection rejected the result",
                    duration_seconds=time.monotonic() - start,
                )

        except Exception as exc:
            self._set_state(AgentState.FAILED)
            result = TaskResult(
                task_id=task_id,
                agent_id=self.agent_id,
                success=False,
                error=str(exc),
                duration_seconds=time.monotonic() - start,
            )
            self._log.error("task.failed", task_id=task_id, error=str(exc))
            raise

        self._log.info("task.complete", task_id=task_id, summary=result.summary())
        return result

    # -- Internals -----------------------------------------------------------

    def _set_state(self, state: AgentState) -> None:
        self.state = state
        self._log.debug("state.change", state=state.value)

    def __repr__(self) -> str:
        return f"<{type(self).__name__} id={self.agent_id} state={self.state.value}>"
