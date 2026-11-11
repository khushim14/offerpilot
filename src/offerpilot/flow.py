"""OfferPilotFlow: draft -> review -> (revise -> review)* -> save.

The reviewer's verdict decides the route. Revisions are capped so the loop
always ends, even if the reviewer is never satisfied.
"""

from pathlib import Path

from crewai.flow import Flow, listen, or_, router, start
from pydantic import BaseModel

from offerpilot.crew import DraftingCrew, Review, RevisionCrew, ReviewCrew

MAX_REVISIONS = 2


class ApplicationState(BaseModel):
    job_posting: str = ""
    resume: str = ""
    company_brief: str = ""
    tailored_resume: str = ""
    cover_letter: str = ""
    reviews: list[Review] = []
    revisions: int = 0
    output_dir: str = "output"


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) or "(none)"


class OfferPilotFlow(Flow[ApplicationState]):
    # ---- Steps -------------------------------------------------------------

    @start()
    def draft(self) -> None:
        brief, resume, letter = self.run_drafting()
        self.state.company_brief = brief
        self.state.tailored_resume = resume
        self.state.cover_letter = letter

    @router(or_(draft, "revised"))
    def review(self) -> str:
        review = self.run_review()
        self.state.reviews.append(review)
        if review.verdict == "APPROVED" or self.state.revisions >= MAX_REVISIONS:
            return "done"
        return "needs_changes"

    @router("needs_changes")
    def revise(self) -> str:
        resume, letter = self.run_revision(self.state.reviews[-1])
        self.state.tailored_resume = resume
        self.state.cover_letter = letter
        self.state.revisions += 1
        return "revised"

    @listen("done")
    def save(self) -> Path:
        out = Path(self.state.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "company_brief.md").write_text(self.state.company_brief, encoding="utf-8")
        (out / "tailored_resume.md").write_text(self.state.tailored_resume, encoding="utf-8")
        (out / "cover_letter.md").write_text(self.state.cover_letter, encoding="utf-8")
        (out / "review.md").write_text(self.review_report(), encoding="utf-8")
        return out

    def review_report(self) -> str:
        lines = ["# Review history", ""]
        for i, r in enumerate(self.state.reviews, 1):
            lines += [
                f"## Round {i}: {r.verdict} ({r.score}/10)",
                "",
                r.summary,
                "",
                "**Resume issues**",
                _bullets(r.resume_issues),
                "",
                "**Cover letter issues**",
                _bullets(r.cover_letter_issues),
                "",
            ]
        return "\n".join(lines)

    # ---- Crew calls (kept separate so tests can replace them) ---------------

    def run_drafting(self) -> tuple[str, str, str]:
        result = DraftingCrew().crew().kickoff(
            inputs={"job_posting": self.state.job_posting, "resume": self.state.resume}
        )
        brief, resume, letter = (t.raw for t in result.tasks_output)
        return brief, resume, letter

    def run_review(self) -> Review:
        result = ReviewCrew().crew().kickoff(
            inputs={
                "review_round": len(self.state.reviews) + 1,
                "job_posting": self.state.job_posting,
                "resume": self.state.resume,
                "tailored_resume": self.state.tailored_resume,
                "cover_letter": self.state.cover_letter,
            }
        )
        return result.pydantic

    def run_revision(self, review: Review) -> tuple[str, str]:
        result = RevisionCrew().crew().kickoff(
            inputs={
                "resume": self.state.resume,
                "tailored_resume": self.state.tailored_resume,
                "cover_letter": self.state.cover_letter,
                "resume_issues": _bullets(review.resume_issues),
                "cover_letter_issues": _bullets(review.cover_letter_issues),
            }
        )
        resume, letter = (t.raw for t in result.tasks_output)
        return resume, letter
