"""Smoke test: the crew builds and is wired as a hierarchical crew. No API calls."""

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from crewai import Process  # noqa: E402

from offerpilot.crew import OfferPilotCrew  # noqa: E402


def test_crew_is_hierarchical_with_four_specialists():
    crew = OfferPilotCrew().crew()
    assert crew.process == Process.hierarchical
    assert crew.manager_agent.role == "Application Orchestrator"
    assert {a.role for a in crew.agents} == {
        "Company Researcher",
        "Resume Tailor",
        "Cover Letter Writer",
        "Application Reviewer",
    }
    assert crew.manager_agent not in crew.agents
    assert len(crew.tasks) == 4
    assert all(t.agent is None for t in crew.tasks)  # orchestrator assigns the work
