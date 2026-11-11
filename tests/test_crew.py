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


def test_research_and_tailoring_run_in_parallel():
    crew = OfferPilotCrew().crew()
    research, tailor, letter, review = crew.tasks
    assert research.async_execution and tailor.async_execution
    assert not letter.async_execution and not review.async_execution
    # The cover letter waits for both parallel tasks and uses their output.
    assert letter.context == [research, tailor]


def test_researcher_has_web_tools(monkeypatch):
    names = lambda: {t.name for t in OfferPilotCrew().company_researcher().tools}  # noqa: E731
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    assert not any("Search" in n for n in names())
    monkeypatch.setenv("SERPER_API_KEY", "test-key")
    assert any("Search" in n for n in names())
    assert any("website" in n.lower() for n in names())
