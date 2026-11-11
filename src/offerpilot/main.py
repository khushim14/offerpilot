"""Command-line entry point: offerpilot --job <url or file> --resume <file>"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv


def run() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Tailor a job application with a crew of AI agents.")
    parser.add_argument("--job", default="inputs/sample_job.md", help="Job posting URL, or path to a text/markdown file.")
    parser.add_argument("--resume", default="inputs/sample_resume.md", help="Path to your resume (text or markdown).")
    args = parser.parse_args()

    from offerpilot.crew import missing_api_key, model_name  # imported late so --help stays fast
    from offerpilot.flow import OfferPilotFlow
    from offerpilot.tools import read_job_posting

    if key := missing_api_key():
        sys.exit(f"{key} is not set for model {model_name()}. Add it to .env (see .env.example).")
    print(f"Using model: {model_name()}")

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
