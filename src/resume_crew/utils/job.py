import requests
from pathlib import Path
from bs4 import BeautifulSoup


def extract_visible_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # remove script and style
    for s in soup(["script", "style", "noscript"]):
        s.decompose()
    # Prefer meaningful text blocks
    parts = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if text:
            parts.append(text)
    # fallback to body text
    if not parts:
        body = soup.body
        if body:
            text = body.get_text(separator=" ", strip=True)
            parts = [text]
    return "\n\n".join(parts)


def fetch_and_save_job(job_url: str, out_dir: Path) -> dict:
    """Fetch job URL, save raw HTML and extracted text into out_dir.

    Returns metadata dict with paths and status.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"job_url": job_url, "status": "failed"}
    try:
        resp = requests.get(job_url, timeout=15)
        resp.raise_for_status()
        html_path = out_dir / "job_description.html"
        text_path = out_dir / "job_description.txt"
        html_path.write_bytes(resp.content)
        extracted = extract_visible_text_from_html(resp.text)
        text_path.write_text(extracted, encoding="utf-8")
        result.update({
            "status": "ok",
            "html_path": str(html_path),
            "text_path": str(text_path),
            "http_status": resp.status_code,
        })
    except Exception as e:
        result.update({"error": str(e)})
    return result
