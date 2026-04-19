import os
import re
from bs4 import BeautifulSoup
from chroma.upsert import clear_chroma_collection, upsert_to_chroma

STRIP_TAGS = ["script", "style", "nav", "footer", "header"]
BOILERPLATE_PHRASES = [
    "Say hello to your colleagues",
    "Create a blog post to share news",
    "End with a bang",
]


def _is_boilerplate(text):
    """Return True if the text matches known Confluence template content."""
    return any(phrase.lower() in text.lower() for phrase in BOILERPLATE_PHRASES)


def _extract_text_from_html(filepath):
    """Parse an HTML file and return cleaned text, or None if empty."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(STRIP_TAGS):
        tag.decompose()
    main_content = soup.find("div", class_="ia-split-view-content")
    if not main_content:
        divs = soup.find_all("div")
        if divs:
            main_content = max(divs, key=lambda d: len(d.get_text(strip=True)))
    text = main_content.get_text(separator=" ", strip=True) if main_content else soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _collect_documents(data_dir):
    """Read all HTML files in data_dir and return (documents, ids, metadatas)."""
    documents, ids, metadatas = [], [], []
    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".html"):
            continue
        text = _extract_text_from_html(os.path.join(data_dir, filename))
        if not text or _is_boilerplate(text):
            print(f"Skipped '{filename}' (empty or boilerplate)")
            continue
        documents.append(text)
        ids.append(filename)
        metadatas.append({"source": filename})
    return documents, ids, metadatas


def ingest_internal_docu():
    """Parse HTML files from Confluence export and upsert to ChromaDB."""
    clear_chroma_collection()
    data_dir = os.environ["DATA_DIR"]
    documents, ids, metadatas = _collect_documents(data_dir)
    upsert_to_chroma(documents, ids, metadatas)
