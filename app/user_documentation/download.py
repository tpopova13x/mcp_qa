import os
import shutil
import zipfile
import requests


def _clear_data_dir(data_dir):
    """Clear all contents of the data directory."""
    if os.path.exists(data_dir):
        for entry in os.listdir(data_dir):
            path = os.path.join(data_dir, entry)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        print(f"Cleared data folder: {data_dir}")
    os.makedirs(data_dir, exist_ok=True)


def _get_auth():
    """Return (archive_url, headers, params) for GitLab API."""
    gitlab_url = os.environ["GITLAB_URL"].rstrip("/")
    project_id = os.environ["GITLAB_PROJECT_ID"]
    branch = os.environ.get("GITLAB_BRANCH", "main")
    path = os.environ.get("GITLAB_PATH", "")

    headers = {"PRIVATE-TOKEN": os.environ["GITLAB_TOKEN"]}
    params = {"sha": branch}
    if path:
        params["path"] = path

    url = f"{gitlab_url}/api/v4/projects/{project_id}/repository/archive.zip"
    return url, headers, params


def _download_archive(url, headers, params, zip_path):
    """Stream the zip archive from GitLab to disk."""
    with requests.get(url, headers=headers, params=params, timeout=60, stream=True) as resp:
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Archive saved to {zip_path}")


def _extract_markdown(zip_path, data_dir):
    """Extract only .md files from the zip archive into data_dir."""
    count = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for file_info in zf.infolist():
            if file_info.is_dir() or not file_info.filename.lower().endswith(".md"):
                continue
            out_path = os.path.join(data_dir, file_info.filename)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with zf.open(file_info) as src, open(out_path, "wb") as dst:
                dst.write(src.read())
            count += 1
    print(f"Extracted {count} markdown files to {data_dir}")


def fetch_files_from_gitlab():
    """Download repository archive from GitLab and extract markdown files."""
    zip_path = os.environ.get("DATA_ARCHIVE", "user_documentation/data/data.zip")
    data_dir = os.path.dirname(zip_path)
    _clear_data_dir(data_dir)
    url, headers, params = _get_auth()
    _download_archive(url, headers, params, zip_path)
    _extract_markdown(zip_path, data_dir)
