# OfferPilot

**A multi-agent job application assistant built with CrewAI.**

Give OfferPilot a job posting and your resume. An orchestrator agent plans the work and delegates it to a crew of specialist agents, which research the company, tailor your resume, write a cover letter, and review everything for accuracy.

## Architecture

```mermaid
flowchart TD
    U[Job posting + resume] --> O[Application Orchestrator<br/>manager agent]
    O -->|delegates| R[Company Researcher]
    O -->|delegates| T[Resume Tailor]
    O -->|delegates| W[Cover Letter Writer]
    O -->|delegates| Q[Application Reviewer]
    R --> O
    T --> O
    W --> O
    Q --> O
    O --> OUT[output/: brief, tailored resume,<br/>cover letter, review]
```

The crew runs as a **hierarchical process**: tasks have no fixed owner, and the orchestrator decides which specialist handles each one, checks the result, and moves on.

| Agent | Job |
|---|---|
| Application Orchestrator | Plans the work, delegates, and checks quality |
| Company Researcher | Pulls out the company's focus, the top skills, and keywords |
| Resume Tailor | Rewrites resume bullets to match the role, without inventing anything |
| Cover Letter Writer | Writes a specific, one-page letter |
| Application Reviewer | Flags invented claims, missing keywords, and tone issues |

## Quick start

```bash
git clone https://github.com/<you>/offerpilot.git
cd offerpilot
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # then paste your Anthropic API key into .env
offerpilot --job inputs/sample_job.md --resume inputs/sample_resume.md
```

Results are written to `output/`.

## Run the tests

```bash
pytest
```

## Roadmap

- [x] Step 1: Hierarchical crew with an orchestrator and four specialists
- [ ] Step 2: Web research tools, reading postings from a URL, and parallel research and tailoring
- [ ] Step 3: A review loop (CrewAI Flow) that sends flagged work back for revision
- [ ] Step 4: A polished CLI and demo

## Tech

Python · CrewAI · Anthropic Claude
