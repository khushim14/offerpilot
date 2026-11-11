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

    from offerpilot.crew import OfferPilotCrew  # imported late so --help stays fast
    from offerpilot.tools import read_job_posting

    inputs = {
        "job_posting": read_job_posting(args.job),
        "resume": Path(args.resume).read_text(encoding="utf-8"),
    }
    Path("output").mkdir(exist_ok=True)
    OfferPilotCrew().crew().kickoff(inputs=inputs)
    print("\nDone. See the output/ folder for the brief, tailored resume, cover letter, and review.")


if __name__ == "__main__":
    run()
