import csv
import os
import time
import psycopg2


def _get_connection():
    host = os.environ["POSTGRES_HOST"]
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    dbname = os.environ["POSTGRES_DB"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]

    for i in range(30):
        try:
            conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
            return conn
        except psycopg2.OperationalError:
            print(f"Waiting for database... ({i+1}/30)")
            time.sleep(2)
    raise Exception("Could not connect to database")


def _ensure_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            id VARCHAR(50) PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            steps TEXT[] NOT NULL
        )
    """)


def clear_tests_table():
    """Drop all rows from the tests table."""
    conn = _get_connection()
    cur = conn.cursor()
    _ensure_table(cur)
    cur.execute("DELETE FROM tests")
    conn.commit()
    deleted = cur.rowcount
    cur.close()
    conn.close()
    print(f"Cleared {deleted} rows from 'tests' table.")


def upsert_tests_to_postgres(tests):
    """Upsert test cases into the PostgreSQL tests table."""
    conn = _get_connection()
    cur = conn.cursor()
    _ensure_table(cur)

    for test in tests:
        cur.execute(
            """
            INSERT INTO tests (id, name, description, steps)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                steps = EXCLUDED.steps
            """,
            (test["id"], test["name"], test.get("description", ""), test["steps"])
        )

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM tests")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"Ingested {total} tests into 'tests' table.")


def _read_csv(data_file):
    """Read CSV and group rows by test ID."""
    tests_by_id = {}
    with open(data_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = row["key"] or row["issueId"]
            if tid not in tests_by_id:
                tests_by_id[tid] = {
                    "id": tid,
                    "name": row.get("summary", ""),
                    "description": row.get("description", ""),
                    "steps": [],
                }
            action = row.get("action", "").strip()
            data = row.get("data", "").strip()
            result = row.get("result", "").strip()
            parts = []
            if action:
                parts.append(f"Action: {action}")
            if data:
                parts.append(f"Data: {data}")
            if result:
                parts.append(f"Expected: {result}")
            if parts:
                tests_by_id[tid]["steps"].append(" | ".join(parts))
    return list(tests_by_id.values())


def ingest_tests():
    """Read CSV and upsert tests to Postgres."""
    clear_tests_table()
    data_file = os.environ["DATA_FILE"]
    tests = _read_csv(data_file)
    upsert_tests_to_postgres(tests)
