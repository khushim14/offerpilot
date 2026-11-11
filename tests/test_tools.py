from offerpilot.tools import read_job_posting


def test_read_job_posting_from_file(tmp_path):
    f = tmp_path / "job.md"
    f.write_text("Software Engineering Intern", encoding="utf-8")
    assert read_job_posting(str(f)) == "Software Engineering Intern"


def test_read_job_posting_from_url(monkeypatch):
    class FakeScraper:
        def __init__(self, website_url):
            self.url = website_url

        def run(self):
            return "Posting text"

    monkeypatch.setattr("offerpilot.tools.ScrapeWebsiteTool", FakeScraper)
    out = read_job_posting("https://example.com/jobs/1")
    assert "Posting text" in out and "https://example.com/jobs/1" in out
