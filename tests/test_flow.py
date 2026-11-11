"""Tests for the draft -> review -> revise loop, with every crew call faked."""

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from offerpilot.crew import Review  # noqa: E402
from offerpilot.flow import MAX_REVISIONS, OfferPilotFlow  # noqa: E402


def needs_changes(score=5):
    return Review(
        verdict="NEEDS_CHANGES",
        score=score,
        summary="Missing keywords.",
        resume_issues=["Add 'REST APIs'"],
        cover_letter_issues=["Too generic"],
    )


APPROVED = Review(verdict="APPROVED", score=9, summary="Strong.")


def make_flow(tmp_path, reviews):
    flow = OfferPilotFlow()
    calls = {"revision": 0, "issues_seen": []}
    queue = list(reviews)

    flow.run_drafting = lambda: ("brief", "resume v0", "letter v0")
    flow.run_review = lambda: queue.pop(0)

    def fake_revision(review):
        calls["revision"] += 1
        calls["issues_seen"].append(review.resume_issues)
        n = calls["revision"]
        return f"resume v{n}", f"letter v{n}"

    flow.run_revision = fake_revision
    flow.kickoff(inputs={"job_posting": "job", "resume": "orig", "output_dir": str(tmp_path)})
    return flow, calls


def test_approved_first_time_skips_revision(tmp_path):
    flow, calls = make_flow(tmp_path, [APPROVED])
    assert calls["revision"] == 0
    assert flow.state.tailored_resume == "resume v0"
    assert (tmp_path / "cover_letter.md").read_text() == "letter v0"


def test_one_revision_then_approved(tmp_path):
    flow, calls = make_flow(tmp_path, [needs_changes(), APPROVED])
    assert calls["revision"] == 1
    assert calls["issues_seen"] == [["Add 'REST APIs'"]]  # reviewer feedback reaches the writers
    assert flow.state.tailored_resume == "resume v1"
    assert len(flow.state.reviews) == 2
    report = (tmp_path / "review.md").read_text()
    assert "Round 1: NEEDS_CHANGES" in report and "Round 2: APPROVED" in report


def test_loop_stops_at_revision_cap(tmp_path):
    reviews = [needs_changes() for _ in range(MAX_REVISIONS + 1)]
    flow, calls = make_flow(tmp_path, reviews)
    assert calls["revision"] == MAX_REVISIONS
    assert len(flow.state.reviews) == MAX_REVISIONS + 1
    for name in ["company_brief.md", "tailored_resume.md", "cover_letter.md", "review.md"]:
        assert (tmp_path / name).exists()
