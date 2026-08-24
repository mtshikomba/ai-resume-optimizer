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

        # Advanced options (hidden by default)
        advanced = st.checkbox("Show advanced options (model & provider)")
        model_choice = None
        provider_choice = None
        provider_api_key = None
        if advanced:
            provider_options = ["OpenAI (Recommended)", "Hugging Face", "Other"]
            selp = st.selectbox("Provider (advanced)", provider_options, index=0)
            if selp == "OpenAI (Recommended)":
                provider_choice = "openai"
            elif selp == "Hugging Face":
                provider_choice = "huggingface"
            else:
                provider_choice = st.text_input("Provider identifier (e.g., my-provider)")

            st.write("Model selection (advanced)")
            model_options = ["Free (free-optimal)", "gpt-3.5-turbo", "gpt-4", "Other"]
            sel = st.selectbox("Model (advanced)", model_options, index=0)
            if sel == "Other":
                model_choice = st.text_input("Model identifier (e.g., my-org/custom-model)")
            elif sel == "Free (free-optimal)":
                model_choice = "free-optimal"
            else:
                model_choice = sel

            # Optional API key input (not persisted to disk)
            provider_api_key = st.text_input("Provider API key (optional)", type="password")

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
        # Save model/provider selection if the user overrode the default
        if advanced and model_choice:
            meta["model"] = model_choice
        if advanced and provider_choice:
            meta["provider"] = provider_choice

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

                # Build subprocess environment
                env = os.environ.copy()
                env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

                # Inject provider API key into the subprocess environment if provided (do not persist to disk)
                if provider_api_key:
                    env_key = None
                    if provider_choice == "openai":
                        env_key = "OPENAI_API_KEY"
                    elif provider_choice == "huggingface":
                        env_key = "HUGGINGFACE_API_KEY"
                    else:
                        env_key = f"{(provider_choice or "").upper()}_API_KEY"
                    if env_key:
                        env[env_key] = provider_api_key

                # Use -u for unbuffered output so we can stream logs
                cmd = [python, "-u", "-m", "resume_crew.runner_cli", str(inputs_json)]
                # Pass provider/model flags to the CLI to ensure the runner sees them
                if advanced and provider_choice:
                    cmd.extend(["--provider", provider_choice])
                if advanced and model_choice:
                    cmd.extend(["--model", model_choice])

                with st.spinner("Running pipeline..."):
                    log_box = st.empty()
                    try:
                        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=str(PROJECT_ROOT), env=env, text=True)
                        # Stream output lines and show live artifact status while waiting
                        import select, time
                        logs = ""
                        status_box = st.empty()
                        log_box = st.empty()

                        artifacts = {
                            "cover_letter": out_dir / "cover_letter.md",
                            "optimized_resume": out_dir / "optimized_resume.md",
                            "final_report": out_dir / "final_report.md",
                            "job_analysis": out_dir / "job_analysis.json",
                            "resume_optimization": out_dir / "resume_optimization.json",
                            "company_research": out_dir / "company_research.json",
                        }

                        start_time = time.time()
                        timeout = 300  # default timeout used by runner

                        # Use select to wait for stdout with timeout, allowing periodic checks
                        while True:
                            # Check for available stdout
                            rlist, _, _ = select.select([proc.stdout], [], [], 1.0)
                            if rlist:
                                line = proc.stdout.readline()
                                if not line:
                                    # EOF
                                    break
                                logs += line
                                log_box.text_area("Pipeline logs", value=logs, height=400)

                            # Update artifact status
                            status_lines = []
                            for name, path in artifacts.items():
                                status = "✅" if path.exists() else "⏳"
                                status_lines.append(f"{status} {name} -> {path.name}")
                            elapsed = int(time.time() - start_time)
                            status_text = "\n".join(status_lines) + f"\n\nElapsed: {elapsed}s"
                            status_box.text(status_text)

                            # Break if process ended
                            if proc.poll() is not None:
                                # read remaining stdout
                                for line in proc.stdout:
                                    if line:
                                        logs += line
                                break

                        proc.wait()
                        logs += f"\nProcess exited with code {proc.returncode}\n"
                        log_box.text_area("Pipeline logs", value=logs, height=400)
                        st.success("Pipeline finished")

                        # After process completes, check for generated artifacts and offer downloads
                        for label, path in artifacts.items():
                            pretty_label = label.replace("_", " ").title()
                            if path.exists():
                                try:
                                    data = path.read_bytes()
                                    st.download_button(label=f"Download: {pretty_label}", data=data, file_name=path.name)
                                except Exception as e:
                                    st.warning(f"Could not read {path.name} for download: {e}")
                            else:
                                st.info(f"{pretty_label} not generated.")

                    except Exception as e:
                        st.error(f"Failed to run pipeline: {e}")


if __name__ == "__main__":
    main()
