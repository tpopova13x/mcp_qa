import logging
import os
from typing import Annotated

import chromadb
import psycopg2.pool
from pydantic import Field
from mcp.server.fastmcp import FastMCP, Context

logging.basicConfig(level=logging.DEBUG)

CHROMA_HOST = os.environ["CHROMA_HOST"]
CHROMA_PORT = int(os.environ["CHROMA_PORT"])
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.environ["POSTGRES_DB"]
POSTGRES_USER = os.environ["POSTGRES_USER"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]

SEARCH_TESTS_QUERY = """
    SELECT id, name, description, steps
    FROM tests
    WHERE
    id ILIKE '%%' || %s || '%%'
    OR to_tsvector(
         'english',
         coalesce(name,'') || ' ' ||
         coalesce(description,'') || ' ' ||
         array_to_string(steps, ' ')
       ) @@ websearch_to_tsquery('english', %s)
    OR word_similarity(
         %s,
         coalesce(name,'') || ' ' ||
         coalesce(description,'') || ' ' ||
         array_to_string(steps, ' ')
       ) > 0.35
"""

chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
pg_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
)

# Ensure pg_trgm extension for fuzzy search
_conn = pg_pool.getconn()
_conn.cursor().execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
_conn.commit()
pg_pool.putconn(_conn)

mcp = FastMCP("mcp-qa", host="0.0.0.0", port=8080)


def _query_chroma(collection_name, query, n_results):
    """Query a ChromaDB collection and return formatted results."""
    collection = chroma_client.get_collection(name=collection_name)
    results = collection.query(query_texts=[query], n_results=n_results)
    output = []
    for doc, meta, distance in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        output.append(f"[source: {meta['source']}, distance: {distance:.4f}]\n{doc}")
    return output


def _query_tests(query):
    """Run full-text search against the tests table and return rows."""
    conn = pg_pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute(SEARCH_TESTS_QUERY, (query, query, query))
        rows = cur.fetchall()
        cur.close()
    finally:
        pg_pool.putconn(conn)
    return rows


def _format_test_rows(rows):
    """Format Postgres test rows into a readable string."""
    output = []
    for row in rows:
        output.append(
            f"ID: {row[0]}\nName: {row[1]}\nDescription: {row[2]}\n"
            f"Steps: {row[3]}"
        )
    return "\n\n---\n\n".join(output)


@mcp.tool()
async def search_user_docu(
    ctx: Context,
    query: Annotated[str, Field(description="The search query to find relevant user documentation")],
    n_results: Annotated[int, Field(description="Number of results to return", default=3)] = 3,
) -> str:
    await ctx.info(f"Searching user docs for: {query}")
    output = _query_chroma("user_docs", query, n_results)
    await ctx.info(f"Found {len(output)} matching user-doc chunks")
    return "\n\n---\n\n".join(output) if output else "No results found."


@mcp.tool()
async def search_internal_docu(
    ctx: Context,
    query: Annotated[str, Field(description="The search query to find relevant internal documentation")],
    n_results: Annotated[int, Field(description="Number of results to return", default=3)] = 3,
) -> str:
    await ctx.info(f"Searching internal docs for: {query}")
    output = _query_chroma("internal_docs", query, n_results)
    await ctx.info(f"Found {len(output)} matching internal-doc chunks")
    return "\n\n---\n\n".join(output) if output else "No results found."


@mcp.tool()
async def search_tests(
    ctx: Context,
    query: Annotated[str, Field(description="Search term to match against test id, name, description, or steps")],
) -> str:
    await ctx.info(f"Searching tests for: {query}")
    rows = _query_tests(query)
    await ctx.info(f"Found {len(rows)} matching tests")
    return _format_test_rows(rows) if rows else "No matching tests found."

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
