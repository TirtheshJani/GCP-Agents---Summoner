"""Research agent that uses Vertex AI to answer questions.

Given a research query the agent:
1. Plans by breaking the query into sub-questions.
2. Executes by sending each sub-question to a Vertex AI generative model.
3. Reflects by checking that every sub-question received a non-empty answer.
"""

from __future__ import annotations

from typing import Any

import structlog

from agents.base_agent import BaseAgent
from config import Settings
from tools.gcp_tools import VertexAITool

logger = structlog.get_logger(__name__)


class ResearchAgent(BaseAgent):
    """Agent that performs research using Vertex AI generative models."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(settings)
        self._vertex = VertexAITool(self.settings)

    @property
    def name(self) -> str:
        return "research"

    def plan(self, task: str) -> str:
        """Break the research query into a numbered list of sub-questions."""
        prompt = (
            "You are a research planner. Given the following research topic, "
            "produce a numbered list of 2-4 focused sub-questions that together "
            "cover the topic comprehensively. Output ONLY the numbered list.\n\n"
            f"Topic: {task}"
        )
        return self._vertex.generate(prompt)

    def execute(self, plan: str) -> Any:
        """Answer each sub-question from the plan."""
        lines = [
            line.strip()
            for line in plan.splitlines()
            if line.strip() and line.strip()[0].isdigit()
        ]
        results: dict[str, str] = {}
        for question in lines:
            answer = self._vertex.generate(
                f"Answer the following research question concisely:\n{question}"
            )
            results[question] = answer
            self.memory.set(question, answer)
        return results

    def reflect(self, task: str, result: Any) -> bool:
        """Check that all sub-questions have non-empty answers."""
        if not isinstance(result, dict) or not result:
            return False
        return all(bool(v) for v in result.values())
