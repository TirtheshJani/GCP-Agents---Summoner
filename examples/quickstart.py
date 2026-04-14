"""Quickstart example: build and run a custom agent locally.

This example works without GCP credentials by using a simple agent that
does not call any cloud services.

Run::

    python examples/quickstart.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.base_agent import BaseAgent  # noqa: E402


class SummaryAgent(BaseAgent):
    """A simple agent that summarises text locally (no GCP needed)."""

    @property
    def name(self) -> str:
        return "summary"

    def plan(self, task: str) -> str:
        words = task.split()
        return f"Summarise the following {len(words)}-word text."

    def execute(self, plan: str) -> Any:
        return f"Plan received: {plan} -- (local echo, no model call)"

    def reflect(self, task: str, result: Any) -> bool:
        return bool(result)


def main() -> None:
    agent = SummaryAgent()
    print(f"Created agent: {agent}")

    result = agent.run("Explain how autonomous AI agents work on cloud platforms.")
    print(f"\nResult: {result.summary()}")
    print(f"Output: {result.output}")


if __name__ == "__main__":
    main()
