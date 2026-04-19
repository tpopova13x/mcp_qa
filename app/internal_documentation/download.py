import os
import re
import shutil
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
    """Return (base_url, auth tuple, headers) for Confluence API."""
    url = os.environ["CONFLUENCE_URL"].rstrip("/")
    auth = (os.environ["CONFLUENCE_EMAIL"], os.environ["CONFLUENCE_JIRA_API_TOKEN"])
    headers = {"Accept": "application/json"}
    return url, auth, headers


def _list_pages(confluence_url, space_key, auth, headers):
    """Paginate through all pages in a Confluence space, return list of (id, title)."""
    base_url = f"{confluence_url}/rest/api/space/{space_key}/content"
    start = 0
    limit = 50
    page_ids = []

    while True:
        params = {"type": "page", "limit": limit, "start": start}
        resp = requests.get(base_url, auth=auth, headers=headers, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", []) or data.get("page", {}).get("results", [])
        if not results:
            break
        for page in results:
            page_ids.append((page["id"], page["title"]))
        if data.get("_links", {}).get("next"):
            start += limit
        else:
            break

    print(f"Found {len(page_ids)} pages in space {space_key}")
    return page_ids


def _download_page(confluence_url, page_id, title, data_dir, auth, headers):
    """Fetch a single page's HTML body and save to data_dir."""
    page_url = f"{confluence_url}/rest/api/content/{page_id}?expand=body.view"
    resp = requests.get(page_url, auth=auth, headers=headers, timeout=60)
    resp.raise_for_status()
    html = resp.json().get("body", {}).get("view", {}).get("value", "")
    if not html or not html.strip():
        print(f"Skipped page '{title}' (empty body)")
        return
    safe_title = re.sub(r"[^a-zA-Z0-9_-]", "_", title)[:50]
    file_path = os.path.join(data_dir, f"{safe_title}_{page_id}.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved page '{title}' to {file_path}")


def fetch_pages_from_confluence():
    """Fetch all pages from a Confluence space and save as HTML files."""
    data_dir = os.environ["DATA_DIR"]
    space_key = os.environ["CONFLUENCE_SPACE_KEY"]
    _clear_data_dir(data_dir)
    confluence_url, auth, headers = _get_auth()
    pages = _list_pages(confluence_url, space_key, auth, headers)
    for page_id, title in pages:
        _download_page(confluence_url, page_id, title, data_dir, auth, headers)
    print(f"Downloaded {len(pages)} pages to {data_dir}")
