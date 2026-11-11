"""Wiring tests for the crews. No API calls."""

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from crewai import Process  # noqa: E402

from offerpilot.crew import DraftingCrew, Review, RevisionCrew, ReviewCrew  # noqa: E402


def test_drafting_crew_is_hierarchical_with_three_specialists():
    crew = DraftingCrew().crew()
    assert crew.process == Process.hierarchical
    assert crew.manager_agent.role == "Application Orchestrator"
    assert {a.role for a in crew.agents} == {"Company Researcher", "Resume Tailor", "Cover Letter Writer"}
    assert crew.manager_agent not in crew.agents
    assert all(t.agent is None for t in crew.tasks)  # orchestrator assigns the work


def test_research_and_tailoring_run_in_parallel():
    research, tailor, letter = DraftingCrew().crew().tasks
    assert research.async_execution and tailor.async_execution
    assert not letter.async_execution
    assert letter.context == [research, tailor]


def test_researcher_has_web_tools(monkeypatch):
    names = lambda: {t.name for t in DraftingCrew().company_researcher().tools}  # noqa: E731
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    assert not any("Search" in n for n in names())
    monkeypatch.setenv("SERPER_API_KEY", "test-key")
    assert any("Search" in n for n in names())
    assert any("website" in n.lower() for n in names())


def test_review_crew_returns_structured_review():
    (task,) = ReviewCrew().crew().tasks
    assert task.output_pydantic is Review
    assert task.agent.role == "Application Reviewer"


def test_revision_crew_sends_fixes_to_original_authors():
    resume_task, letter_task = RevisionCrew().crew().tasks
    assert resume_task.agent.role == "Resume Tailor"
    assert letter_task.agent.role == "Cover Letter Writer"
    assert letter_task.context == [resume_task]
