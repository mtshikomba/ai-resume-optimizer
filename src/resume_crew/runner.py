import json
from pathlib import Path
from resume_crew.crew import ResumeCrew


def run_from_inputs(inputs_json_path: str) -> dict:
    """Run the ResumeCrew pipeline using the inputs.json produced by the Streamlit UI.

    inputs_json_path: path to inputs.json file saved by the UI (contains company, job_title, job_url, resume_file, custom_cover_file)
    Returns a dict with run status and output folder.
    """
    inputs_path = Path(inputs_json_path)
    if not inputs_path.exists():
        raise FileNotFoundError(f"Inputs file not found: {inputs_json_path}")

    meta = json.loads(inputs_path.read_text(encoding="utf-8"))
    # Determine output folder (inputs.json parent)
    out_dir = inputs_path.parent

    resume_file = meta.get("resume_file")
    company = meta.get("company")
    job_title = meta.get("job_title")
    job_url = meta.get("job_url") or meta.get("job_url_fetch", {}).get("job_url")
    custom_cover = None
    if meta.get("custom_cover_file"):
        try:
            custom_cover = Path(meta.get("custom_cover_file")).read_text(encoding="utf-8")
        except Exception:
            custom_cover = None

    # Instantiate the crew with resume and output directory
    crew = ResumeCrew(resume_pdf_path=resume_file, out_dir=str(out_dir))

    # Prepare inputs for the crew kickoff
    kickoff_inputs = {
        "job_url": job_url or "",
        "company_name": company or "",
    }

    # Optionally add cover text into inputs so agents can use it
    if custom_cover:
        kickoff_inputs["custom_cover_text"] = custom_cover

    # Run the crew pipeline
    # Note: depending on CrewAI runtime, kickoff may be blocking.
    try:
        crew.crew().kickoff(inputs=kickoff_inputs)
        return {"status": "ok", "output_dir": str(out_dir)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
