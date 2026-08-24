from pathlib import Path
import re


def slugify(text: str) -> str:
    """Create a simple slug suitable for filenames from arbitrary text."""
    text = (text or "").strip().lower()
    # remove unsafe characters
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    # collapse whitespace to underscores
    text = re.sub(r"\s+", "_", text)
    # collapse repeated underscores/dashes
    text = re.sub(r"[_-]+", "_", text)
    return text.strip("_")


def save_uploaded_file(uploaded_file, dest_path: Path) -> Path:
    """Save a Streamlit uploaded file (UploadedFile) to dest_path and return the path."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    # uploaded_file implements getbuffer()
    with open(dest_path, "wb") as out:
        out.write(uploaded_file.getbuffer())
    return dest_path


def get_project_root() -> Path:
    # src/resume_crew/utils/io.py -> project root is four parents up: utils -> resume_crew -> src -> project-root
    return Path(__file__).resolve().parents[3]


def get_knowledge_resumes() -> list:
    """Return a list of relative paths (from project root) to PDF resumes in the knowledge folder."""
    root = get_project_root()
    knowledge_dir = root / "knowledge"
    results = []
    if knowledge_dir.exists():
        for p in knowledge_dir.rglob("*.pdf"):
            try:
                results.append(str(p.relative_to(root)))
            except Exception:
                results.append(str(p))
    return results
