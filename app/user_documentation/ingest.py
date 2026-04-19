import os
import zipfile
from chroma.upsert import clear_chroma_collection, upsert_to_chroma


def _collect_documents(zip_path):
    """Read all .md files from the zip archive and return (documents, ids, metadatas)."""
    documents, ids, metadatas = [], [], []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".md"):
                continue
            content = zf.read(name).decode("utf-8").strip()
            if not content:
                continue
            documents.append(content)
            ids.append(name)
            metadatas.append({"source": name})
    return documents, ids, metadatas


def ingest_user_docu():
    """Extract markdown files from zip archive and upsert to ChromaDB."""
    clear_chroma_collection()
    zip_path = os.environ["DATA_ARCHIVE"]
    documents, ids, metadatas = _collect_documents(zip_path)
    upsert_to_chroma(documents, ids, metadatas)
