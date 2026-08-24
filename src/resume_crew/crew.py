from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from .models import (
    JobRequirements,
    ResumeOptimization,
    CompanyResearch
)


@CrewBase
class ResumeCrew():
    """ResumeCrew for resume optimization and interview preparation"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self, resume_pdf_path: str | None = None, out_dir: str | None = None, model: str | None = None) -> None:
        """Initialize ResumeCrew.

        resume_pdf_path: path to a PDF resume file (relative to project root or absolute). If None, falls back to the sample CV_Mohan.pdf in the knowledge folder.
        out_dir: directory where task outputs should be written. If None, defaults to 'output/'.
        """
        import os
        # Determine resume knowledge source
        if resume_pdf_path:
            self.resume_pdf = PDFKnowledgeSource(file_paths=resume_pdf_path)
        else:
            self.resume_pdf = PDFKnowledgeSource(file_paths="CV_Mohan.pdf")

        # Resolve model: parameter > env var > default
        self.model = model or os.getenv("RESUME_CREW_MODEL") or "free-optimal"

        # Output directory for generated files
        from pathlib import Path
        self.out_dir = Path(out_dir) if out_dir else Path("output")
        self.out_dir.mkdir(parents=True, exist_ok=True)

    @agent
    def resume_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_analyzer'],
            verbose=True,
        llm=LLM(self.model),
            knowledge_sources=[self.resume_pdf]
        )
    
    @agent
    def job_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['job_analyzer'],
            verbose=True,
            tools=[ScrapeWebsiteTool()],
        llm=LLM(self.model)
        )

    @agent
    def company_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['company_researcher'],
            verbose=True,
            tools=[SerperDevTool()],
        llm=LLM(self.model),
            knowledge_sources=[self.resume_pdf]
        )

    @agent
    def resume_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['resume_writer'],
            verbose=True,
        llm=LLM(self.model)
        )

    @agent
    def cover_letter_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['cover_letter_writer'],
            verbose=True,
            llm=LLM(self.model)
        )

    @agent
    def report_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['report_generator'],
            verbose=True,
            llm=LLM(self.model)
        )

    @task
    def analyze_job_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_job_task'],
            output_file=str(self.out_dir / 'job_analysis.json'),
            output_pydantic=JobRequirements
        )

    @task
    def optimize_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config['optimize_resume_task'],
            output_file=str(self.out_dir / 'resume_optimization.json'),
            output_pydantic=ResumeOptimization
        )

    @task
    def research_company_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_company_task'],
            output_file=str(self.out_dir / 'company_research.json'),  
            output_pydantic=CompanyResearch
        )

    @task
    def generate_resume_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_resume_task'],
            output_file=str(self.out_dir / 'optimized_resume.md')
        )

    @task
    def generate_cover_letter_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_cover_letter_task'],
            output_file=str(self.out_dir / 'cover_letter.md')
        )

    @task
    def generate_report_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_report_task'],
            output_file=str(self.out_dir / 'final_report.md')
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
            process=Process.sequential,
            knowledge_sources=[self.resume_pdf]
        )
