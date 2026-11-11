"""Command-line entry point: offerpilot --job <url or file> --resume <file>"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def run() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Tailor a job application with a crew of AI agents.")
    parser.add_argument("--job", default="inputs/sample_job.md", help="Job posting URL, or path to a text/markdown file.")
    parser.add_argument("--resume", default="inputs/sample_resume.md", help="Path to your resume (text or markdown).")
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.")

    from offerpilot.flow import OfferPilotFlow  # imported late so --help stays fast
    from offerpilot.tools import read_job_posting

    flow = OfferPilotFlow()
    flow.kickoff(
        inputs={
            "job_posting": read_job_posting(args.job),
            "resume": Path(args.resume).read_text(encoding="utf-8"),
        }
    )
    final = flow.state.reviews[-1]
    print(
        f"\nDone after {flow.state.revisions} revision(s). Final review: {final.verdict} ({final.score}/10)."
        "\nSee the output/ folder for the brief, tailored resume, cover letter, and review history."
    )


if __name__ == "__main__":
    run()
