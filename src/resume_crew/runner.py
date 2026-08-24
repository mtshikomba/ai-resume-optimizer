import json
from pathlib import Path
from resume_crew.crew import ResumeCrew


def run_from_inputs(inputs_json_path: str, timeout_seconds: int = 300, poll_interval: float = 2.0, model_override: str | None = None) -> dict:
    """Run the ResumeCrew pipeline using the inputs.json produced by the Streamlit UI.

    inputs_json_path: path to inputs.json file saved by the UI (contains company, job_title, job_url, resume_file, custom_cover_file)
    timeout_seconds: how long to wait for expected artifacts to appear after kickoff (seconds). Default 300s.
    poll_interval: seconds between checks for output files. Default 2s.

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

    # Determine model override from inputs (if any); CLI-provided model_override takes precedence
    meta_model = meta.get("model")
    model_to_use = model_override or meta_model

    # Instantiate the crew with resume, output directory, and optional model
    crew = ResumeCrew(resume_pdf_path=resume_file, out_dir=str(out_dir), model=model_to_use)

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

        # After kickoff, wait for expected output files to appear (polling)
        expected = {
            "job_analysis": out_dir / "job_analysis.json",
            "resume_optimization": out_dir / "resume_optimization.json",
            "company_research": out_dir / "company_research.json",
            "optimized_resume": out_dir / "optimized_resume.md",
            "cover_letter": out_dir / "cover_letter.md",
            "final_report": out_dir / "final_report.md",
        }

        import time
        start = time.time()
        found = set()
        outputs = {}

        while True:
            for name, path in expected.items():
                if name in found:
                    continue
                if path.exists():
                    found.add(name)
                    outputs[name] = str(path)
            if len(found) == len(expected):
                status = "ok"
                missing = []
                break
            elapsed = time.time() - start
            if elapsed >= timeout_seconds:
                # timeout reached
                missing = [n for n in expected.keys() if n not in found]
                status = "partial" if outputs else "missing"
                break
            time.sleep(poll_interval)

        return {"status": status, "output_dir": str(out_dir), "outputs": outputs, "missing": missing, "waited_seconds": int(time.time()-start)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
