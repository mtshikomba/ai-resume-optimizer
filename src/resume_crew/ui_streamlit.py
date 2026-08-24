import streamlit as st
from pathlib import Path
import shutil
import json
from resume_crew.utils.io import slugify, save_uploaded_file, get_knowledge_resumes

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def main():
    st.title("Resume Optimization — Streamlit UI")
    st.write("Upload a job description (file or URL), choose or upload a resume, optionally provide custom cover letter text, and generate outputs.")

    with st.form("inputs"):
        company = st.text_input("Company name", "")
        job_title = st.text_input("Job title", "")
        job_url = st.text_input("Job posting URL (optional)")
        job_file = st.file_uploader("Upload job description file (PDF / TXT / MD)", type=["pdf", "txt", "md"])

        resume_source = st.radio("Resume source", ("Use sample resume from knowledge/", "Upload my resume"))
        selected_resume = None
        uploaded_resume = None
        if resume_source.startswith("Use"):
            choices = get_knowledge_resumes()
            if choices:
                selected_resume = st.selectbox("Select sample resume", choices)
            else:
                st.info("No sample resumes found in the knowledge folder. Upload instead.")
                uploaded_resume = st.file_uploader("Upload resume (PDF)", type=["pdf"])
        else:
            uploaded_resume = st.file_uploader("Upload resume (PDF)", type=["pdf"])

        custom_cover = st.text_area("Optional: custom text to mention in the cover letter", height=150)
        submitted = st.form_submit_button("Generate")

    if submitted:
        if not company:
            st.error("Company name is required")
            return
        if not (job_title or job_url or job_file):
            st.error("Please provide at least a job title, a job URL, or upload a job description file.")
            return

        slug = slugify(f"{company} {job_title or 'job'}")
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = PROJECT_ROOT / "output" / f"{slug}_{timestamp}"
        out_dir.mkdir(parents=True, exist_ok=True)

        meta = {
            "company": company,
            "job_title": job_title,
            "job_url": job_url or "",
            "custom_cover_text_provided": bool(custom_cover),
        }

        # Save job file if uploaded
        if job_file:
            job_dest = out_dir / f"job_description{Path(job_file.name).suffix}"
            save_uploaded_file(job_file, job_dest)
            meta["job_file"] = str(job_dest)

        # If a job URL was provided, try to fetch and extract text
        if job_url:
            try:
                from resume_crew.utils.job import fetch_and_save_job
                fetch_meta = fetch_and_save_job(job_url, out_dir)
                meta["job_url_fetch"] = fetch_meta
            except Exception as e:
                meta["job_url_fetch_error"] = str(e)

        # Handle resume
        if uploaded_resume:
            resume_dest = out_dir / f"resume{Path(uploaded_resume.name).suffix}"
            save_uploaded_file(uploaded_resume, resume_dest)
            meta["resume_file"] = str(resume_dest)
        elif selected_resume:
            # selected_resume may be a relative path (e.g., 'knowledge/CV_Mohan.pdf') or an absolute path.
            sel_path = Path(selected_resume)
            if sel_path.is_absolute():
                src = sel_path
            else:
                # Ensure we join with PROJECT_ROOT and normalize leading slashes
                src = (PROJECT_ROOT / selected_resume.lstrip("/"))
            if not src.exists():
                st.error(f"Selected resume not found: {src}. Please upload a resume or verify the knowledge folder path.")
            else:
                dest = out_dir / src.name
                shutil.copy(src, dest)
                meta["resume_file"] = str(dest)
        else:
            st.warning("No resume selected or uploaded — the pipeline may fail without a resume.")

        # Save custom cover text
        if custom_cover:
            with open(out_dir / "custom_cover.txt", "w", encoding="utf-8") as f:
                f.write(custom_cover)
            meta["custom_cover_file"] = str(out_dir / "custom_cover.txt")

        # Save metadata
        with open(out_dir / "inputs.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        st.success(f"Inputs saved to {out_dir}")
        st.write("Files created:")
        for p in sorted(out_dir.iterdir()):
            st.write(f"- {p.name}")

        st.info("Inputs saved. You can now run the pipeline for this input folder below.")

        # Run pipeline now
        run_btn = st.button("Run pipeline now")
        if run_btn:
            inputs_json = out_dir / "inputs.json"
            if not inputs_json.exists():
                st.error("inputs.json not found; cannot run pipeline.")
            else:
                st.info("Starting pipeline — streaming logs below.")
                import subprocess, sys, os
                python = sys.executable or "python"
                env = os.environ.copy()
                env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
                # Use -u for unbuffered output so we can stream logs
                cmd = [python, "-u", "-m", "resume_crew.runner_cli", str(inputs_json)]
                with st.spinner("Running pipeline..."):
                    log_box = st.empty()
                    try:
                        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(PROJECT_ROOT), env=env, text=True)
                        # Stream output lines
                        logs = ""
                        for line in proc.stdout:
                            logs += line
                            log_box.text_area("Pipeline logs", value=logs, height=400)
                        proc.wait()
                        logs += f"\nProcess exited with code {proc.returncode}\n"
                        log_box.text_area("Pipeline logs", value=logs, height=400)
                        st.success("Pipeline finished")

                        # After process completes, check for generated artifacts and offer downloads
                        artifacts = {
                            "Cover Letter": out_dir / "cover_letter.md",
                            "Optimized Resume": out_dir / "optimized_resume.md",
                            "Final Report": out_dir / "final_report.md",
                            "Job Analysis (JSON)": out_dir / "job_analysis.json",
                            "Resume Optimization (JSON)": out_dir / "resume_optimization.json",
                            "Company Research (JSON)": out_dir / "company_research.json",
                        }
                        for label, path in artifacts.items():
                            if path.exists():
                                try:
                                    data = path.read_bytes()
                                    st.download_button(label=f"Download: {label}", data=data, file_name=path.name)
                                except Exception as e:
                                    st.warning(f"Could not read {path.name} for download: {e}")
                            else:
                                st.info(f"{label} not generated yet.")

                    except Exception as e:
                        st.error(f"Failed to run pipeline: {e}")


if __name__ == "__main__":
    main()
