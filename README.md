# Resume Optimization with CrewAI

![Resume Optimization System Architecture](docs/architecture-diagam.svg)

An AI-powered tool that optimizes your resume for specific job applications using multiple AI agents. Built with [CrewAI](https://crewai.com).

## What It Does

1. **Job Analysis**: Analyzes job requirements, skills, and qualifications
2. **Resume Scoring**: Calculates match scores for technical skills, experience, and qualifications
3. **Optimization**: Suggests specific improvements to increase your match score
4. **Company Research**: Provides company insights for interview preparation

## Installation

1. Clone the repository and install dependencies:

    ```bash
    git clone https://github.com/tonykipkemboi/resume-optimization-crew.git
    cd resume-optimization-crew
    ```

2. Create a virtual environment and install dependencies:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    crewai install
    ```

## Environment Setup

1. Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```

2. Add your API keys to `.env`:
    - Required:
        - `OPENAI_API_KEY`: OpenAI API key
        - `SERPER_API_KEY`: Serper API key for web search
    - Optional:
        - See `.env.example` for additional optional APIs

## Quick Start

1. Save your resume as PDF in the project root under the `knowledge/` directory:
    - Feel free to use the sample resume provided in `knowledge/knowledge/CV_Mohan.pdf`
    - I got it from [here](https://www.hbs.edu/doctoral/Documents/job-market/CV_Mohan.pdf)

2. Fill in the input data in `main.py`:
    - `job_url`: URL of the job posting (e.g., 'https://www.mckinsey.com/careers/search-jobs/jobs/associate-15178')
    - `company_name`: Name of the company (e.g., 'Mckinsey & Co.')

3. Run the optimization crew:
    ```bash
    crewai run
    ```

## Output Files

The tool generates three JSON files in the `output` directory:

- `job_analysis.json`: Detailed job requirements and match scoring
- `resume_optimization.json`: Specific suggestions to improve your resume
- `company_research.json`: Company insights for interview prep

## Architecture

The system uses three specialized AI agents:

1. **Job Analyzer**: Extracts and analyzes job requirements
2. **Resume Analyzer**: Scores resume match and suggests improvements
3. **Company Researcher**: Gathers company information for interviews

## Requirements

- Python `>= 3.10` and `< 3.13`
- PDF resume file
- Job posting URL
- Company name

## Support

- [CrewAI Documentation](https://docs.crewai.com)
- [Community Forum](https://community.crewai.com)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

## Running the Streamlit UI

This project now includes a Streamlit-based UI to upload/select a resume, provide a job description (URL or file), optionally add custom cover-letter text, and run the CrewAI pipeline to produce analysis, an optimized resume, a cover letter, and a final report.

Recommended ways to run the UI

1) Using your existing Docker image (quick, recommended if you already have tonykip/crewai:cli):

```bash
# run interactively and expose port 8501
docker run --rm -it -p 8501:8501 -v "$(pwd)":/work -w /work tonykip/crewai:cli bash -lc "\
  python -m pip install --upgrade pip setuptools wheel && \
  pip install --no-cache-dir streamlit requests beautifulsoup4 && \
  export PYTHONPATH=/work/src && \
  streamlit run src/resume_crew/ui_streamlit.py --server.port 8501 --server.headless true --server.enableCORS false"
```

Open http://localhost:8501 in your browser and use the form.

2) Docker Compose (project contains a Dockerfile and docker-compose.yml):

```bash
# build and run (maps host 8501 to container 8501)
docker-compose up --build
```

3) Using uv (the project's package manager) inside a Linux container or local environment:

```bash
# sync the environment (may install many dependencies)
uv sync --no-dev
# Run streamlit in the uv-managed environment
uv run -- streamlit run src/resume_crew/ui_streamlit.py --server.port 8501 --server.headless true
```

4) Local virtualenv (developer workflow):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install streamlit requests beautifulsoup4
streamlit run src/resume_crew/ui_streamlit.py
```

How the runner and "Run pipeline now" work

- The UI saves inputs to a timestamped run folder under `output/` (format: output/<company>_<job>_YYYYMMDD_HHMMSS/).
- Model selection: by default the system uses a free optimal model. You can override the model via the UI advanced options or set the environment variable RESUME_CREW_MODEL to change the default model used by agents.
- Click "Run pipeline now" in the UI to invoke the runner CLI; the UI streams logs and shows live artifact status.
- The runner CLI is available as a module entry point: `python -m resume_crew.runner_cli <path/to/inputs.json>`
- The runner waits for expected artifacts (default timeout 300s) and reports status; you can pass `--timeout` and `--poll` to the CLI.

Example runner CLI usage:

```bash
python -m resume_crew.runner_cli output/mycompany_myjob_20260825_120000/inputs.json --timeout 600 --poll 2.0
```

Expected outputs

When a run completes, the following artifacts are created in the run folder (if generated by agents):

- cover_letter.md — a one-page tailored cover letter in markdown
- optimized_resume.md — the generated optimized resume in markdown
- final_report.md — an executive summary report in markdown
- job_analysis.json, resume_optimization.json, company_research.json — structured JSON outputs

Troubleshooting

- If Streamlit is not reachable, ensure port 8501 is exposed and not blocked by firewall or other processes.
- If the runner reports missing artifacts, check the UI logs for agent errors and inspect the run folder for saved logs or partial outputs.
- For macOS users: some dependencies (onnxruntime, etc.) may not have wheels for older macOS versions; running inside a Linux container is the recommended path for reproducible installs.

If you encounter problems, open an issue or contact the maintainers with the run folder and CLI output.
