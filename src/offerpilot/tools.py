"""Tools for the crew, and helpers for reading inputs."""

import os
from pathlib import Path

from crewai_tools import ScrapeWebsiteTool, SerperDevTool


def research_tools() -> list:
    """Web tools for the Company Researcher. Search is enabled only if SERPER_API_KEY is set."""
    tools: list = [ScrapeWebsiteTool()]
    if os.getenv("SERPER_API_KEY"):
        tools.append(SerperDevTool())
    return tools


def read_job_posting(source: str) -> str:
    """Return the posting text from a URL or a local file path."""
    if source.startswith(("http://", "https://")):
        text = ScrapeWebsiteTool(website_url=source).run()
        return f"(Fetched from {source})\n\n{text}"
    return Path(source).read_text(encoding="utf-8")
