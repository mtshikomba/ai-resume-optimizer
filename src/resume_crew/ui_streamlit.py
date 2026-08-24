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

        st.info("Next steps: wire these inputs into the CrewAI pipeline (next task).")


if __name__ == "__main__":
    main()
