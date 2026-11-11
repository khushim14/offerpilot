"""The OfferPilot crews.

- DraftingCrew: the orchestrator delegates research, resume tailoring, and the
  cover letter to specialists (hierarchical process).
- ReviewCrew: the reviewer scores the drafts and returns structured feedback.
- RevisionCrew: the resume tailor and cover letter writer fix flagged issues.

The flow in flow.py connects them into a draft -> review -> revise loop.
"""

import os
from typing import Literal

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field

from offerpilot.tools import research_tools

DEFAULT_MODEL = "anthropic/claude-sonnet-5-5"


# Which environment variable(s) each provider needs. Ollama runs locally and needs none.
PROVIDER_KEYS = {
    "anthropic": ("ANTHROPIC_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "openai": ("OPENAI_API_KEY",),
    "groq": ("GROQ_API_KEY",),
    "ollama": (),
}


def model_name() -> str:
    return os.getenv("OFFERPILOT_MODEL") or DEFAULT_MODEL


def missing_api_key() -> str | None:
    """Return the name of the key the chosen model needs but doesn't have, or None if all set."""
    provider = model_name().split("/", 1)[0]
    keys = PROVIDER_KEYS.get(provider, ())
    if keys and not any(os.getenv(k) for k in keys):
        return keys[0]
    return None


def _agent(config: dict, **kwargs) -> Agent:
    return Agent(config=config, llm=model_name(), verbose=True, **kwargs)


class Review(BaseModel):
    """Structured output from the reviewer, used by the flow to decide what happens next."""

    verdict: Literal["APPROVED", "NEEDS_CHANGES"]
    score: int = Field(ge=0, le=10)
    summary: str
    resume_issues: list[str] = []
    cover_letter_issues: list[str] = []


@CrewBase
class DraftingCrew:
    """Hierarchical crew. The orchestrator plans and delegates; specialists do the work."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def company_researcher(self) -> Agent:
        return _agent(self.agents_config["company_researcher"], tools=research_tools())

    @agent
    def resume_tailor(self) -> Agent:
        return _agent(self.agents_config["resume_tailor"])

    @agent
    def cover_letter_writer(self) -> Agent:
        return _agent(self.agents_config["cover_letter_writer"])

    # Not an @agent: the manager must stay out of the worker list.
    def orchestrator(self) -> Agent:
        return _agent(self.agents_config["orchestrator"], allow_delegation=True)

    # No agent assigned: the orchestrator decides who does each task.
    # Research and resume tailoring don't depend on each other, so they run in parallel.

    @task
    def research_company(self) -> Task:
        return Task(config=self.tasks_config["research_company"], async_execution=True)

    @task
    def tailor_resume(self) -> Task:
        return Task(config=self.tasks_config["tailor_resume"], async_execution=True)

    @task
    def write_cover_letter(self) -> Task:
        return Task(
            config=self.tasks_config["write_cover_letter"],
            context=[self.research_company(), self.tailor_resume()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.orchestrator(),
            verbose=True,
        )


@CrewBase
class ReviewCrew:
    """A single reviewer that returns a structured Review."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def reviewer(self) -> Agent:
        return _agent(self.agents_config["reviewer"])

    @task
    def review_application(self) -> Task:
        return Task(
            config=self.tasks_config["review_application"],
            agent=self.reviewer(),
            output_pydantic=Review,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)


@CrewBase
class RevisionCrew:
    """The original authors fix the issues the reviewer flagged."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def resume_tailor(self) -> Agent:
        return _agent(self.agents_config["resume_tailor"])

    @agent
    def cover_letter_writer(self) -> Agent:
        return _agent(self.agents_config["cover_letter_writer"])

    @task
    def revise_resume(self) -> Task:
        return Task(config=self.tasks_config["revise_resume"], agent=self.resume_tailor())

    @task
    def revise_cover_letter(self) -> Task:
        return Task(
            config=self.tasks_config["revise_cover_letter"],
            agent=self.cover_letter_writer(),
            context=[self.revise_resume()],
        )

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)
