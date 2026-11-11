"""The OfferPilot crew: an orchestrator that delegates to four specialist agents."""

import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

DEFAULT_MODEL = "anthropic/claude-sonnet-5-5"


def model_name() -> str:
    return os.getenv("OFFERPILOT_MODEL", DEFAULT_MODEL)


@CrewBase
class OfferPilotCrew:
    """Hierarchical crew. The orchestrator plans and delegates; specialists do the work."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # ---- Specialists -------------------------------------------------------

    @agent
    def company_researcher(self) -> Agent:
        return Agent(config=self.agents_config["company_researcher"], llm=model_name(), verbose=True)

    @agent
    def resume_tailor(self) -> Agent:
        return Agent(config=self.agents_config["resume_tailor"], llm=model_name(), verbose=True)

    @agent
    def cover_letter_writer(self) -> Agent:
        return Agent(config=self.agents_config["cover_letter_writer"], llm=model_name(), verbose=True)

    @agent
    def reviewer(self) -> Agent:
        return Agent(config=self.agents_config["reviewer"], llm=model_name(), verbose=True)

    # ---- Orchestrator (not an @agent: the manager must stay out of the worker list)

    def orchestrator(self) -> Agent:
        return Agent(
            config=self.agents_config["orchestrator"],
            llm=model_name(),
            allow_delegation=True,
            verbose=True,
        )

    # ---- Tasks (no agent assigned: the orchestrator decides who does each one)

    @task
    def research_company(self) -> Task:
        return Task(config=self.tasks_config["research_company"], output_file="output/company_brief.md")

    @task
    def tailor_resume(self) -> Task:
        return Task(config=self.tasks_config["tailor_resume"], output_file="output/tailored_resume.md")

    @task
    def write_cover_letter(self) -> Task:
        return Task(config=self.tasks_config["write_cover_letter"], output_file="output/cover_letter.md")

    @task
    def review_application(self) -> Task:
        return Task(config=self.tasks_config["review_application"], output_file="output/review.md")

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_agent=self.orchestrator(),
            verbose=True,
        )
