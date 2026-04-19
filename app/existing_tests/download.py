import csv
import os
import shutil
import requests

BASE = "https://xray.cloud.getxray.app/api/v2"

GRAPHQL_QUERY = """
query GetTests($jql: String!, $limit: Int!) {
    getExpandedTests(jql: $jql, limit: $limit) {
        total
        start
        limit
        results {
            issueId
            testType {
                name
                kind
            }
            steps {
                parentTestIssueId
                calledTestIssueId
                id
                data
                action
                result
                attachments {
                    id
                    filename
                }
            }
            jira(fields: ["key", "summary", "description"])
            warnings
        }
    }
}
"""


def _authenticate():
    """Authenticate with Xray Cloud API and return a bearer token."""
    resp = requests.post(
        f"{BASE}/authenticate",
        json={
            "client_id": os.environ["XRAY_CLIENT_ID"],
            "client_secret": os.environ["XRAY_CLIENT_SECRET"],
        },
    )
    resp.raise_for_status()
    return resp.text.strip('"')


def _fetch_tests(token):
    """Fetch tests from Xray Cloud GraphQL API."""
    jql = os.environ.get("XRAY_JQL", "project = MBA AND labels = mcp")
    resp = requests.post(
        f"{BASE}/graphql",
        json={"query": GRAPHQL_QUERY, "variables": {"jql": jql, "limit": 100}},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    resp.raise_for_status()
    response_json = resp.json()
    if "errors" in response_json:
        raise RuntimeError(response_json["errors"])
    return response_json["data"]["getExpandedTests"]["results"]


def _write_csv(tests, output_path):
    """Write tests to a CSV file."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "issueId", "key", "summary", "description",
            "step_id", "action", "data", "result",
        ])

        for test in tests:
            jira = test.get("jira") or {}
            steps = test.get("steps") or []
            common = [
                test.get("issueId"),
                jira.get("key"),
                jira.get("summary"),
                jira.get("description"),
            ]

            if not steps:
                writer.writerow(common + ["", "", "", ""])
                continue

            for step in steps:
                writer.writerow(common + [
                    step.get("id"),
                    step.get("action"),
                    step.get("data"),
                    step.get("result"),
                ])


def _clear_data_dir(output_path):
    """Clear all contents of the data directory."""
    data_dir = os.path.dirname(output_path)
    if os.path.exists(data_dir):
        for entry in os.listdir(data_dir):
            path = os.path.join(data_dir, entry)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        print(f"Cleared data folder: {data_dir}")
    os.makedirs(data_dir, exist_ok=True)


def export_xray_tests_to_csv():
    """Export Xray tests to CSV using Xray Cloud GraphQL API."""
    output_path = os.environ.get("XRAY_CSV_PATH", "existing_tests/data/tests.csv")
    _clear_data_dir(output_path)
    token = _authenticate()
    tests = _fetch_tests(token)
    _write_csv(tests, output_path)
    print(f"Exported Xray tests to {output_path}")

