# MCP QA

An MCP (Model Context Protocol) server that exposes QA-related data sources — user documentation, internal documentation, and test cases — as searchable tools for AI assistants.

## Architecture

```
┌─────────────┐     ┌───────────┐     ┌────────────┐
│  MCP Client │────▶│ MCP Server│────▶│  ChromaDB   │  (user_docs, internal_docs)
│  (Copilot)  │     │  :8080    │     │  :8000      │
└─────────────┘     └───────────┘     └────────────┘
                         │
                         └───────────▶┌────────────┐
                                      │ PostgreSQL  │  (tests)
                                      │  :5432      │
                                      └────────────┘
```

## MCP Tools

| Tool | Description | Data Source |
|------|-------------|-------------|
| `search_user_docu` | Search user-facing documentation | ChromaDB (`user_docs` collection) |
| `search_internal_docu` | Search internal/API documentation | ChromaDB (`internal_docs` collection) |
| `search_tests` | Search test cases by id, name, role, or steps | PostgreSQL (`tests` table) |

## Project Structure

```
├── docker-compose.yml          # All services with profiles
├── .env                        # Environment variables & credentials
├── requirements.txt
├── app/
│   ├── ingest.py               # Unified ingest CLI (user-docu | internal-docu | tests)
│   ├── Dockerfile.ingest       # Dockerfile for all ingest operations
│   ├── mcp_server/
│   │   ├── server.py           # MCP server with 3 tools
│   │   └── Dockerfile
│   ├── user_documentation/     # Local user docs (markdown in zip)
│   ├── internal_documentation/ # Local internal docs (PDFs)
│   └── existing_tests/         # Local test data (JSON)
├── storage/                    # Docker volumes (chroma-data, postgres-data)
├── tests/                      # Test & query scripts
│   ├── test_mcp_server.py
│   ├── query_user_docu.py
│   └── query_int_docu.py
└── .vscode/
    └── mcp.json                # VS Code Copilot MCP integration
```

## Quick Start

### 1. Configure environment

Copy and edit `.env` with your credentials. The defaults work for local-only mode.

### 2. Choose a mode

The project supports 3 operational modes via Docker Compose profiles:

#### Mode 1: No ingestion (data already loaded)

```bash
docker compose up -d
```

Starts only the infrastructure (ChromaDB, PostgreSQL) and the MCP server.

#### Mode 2: Ingest from local files

```bash
docker compose --profile ingest up
```

Ingests data from local files into the databases:
- **User docs** — markdown files from `app/user_documentation/data.zip`
- **Internal docs** — PDFs from `app/internal_documentation/data/`
- **Tests** — JSON from `app/existing_tests/data/tests.json`

#### Mode 3: Download from external sources & ingest

```bash
docker compose --profile download-and-ingest up
```

Downloads and ingests data from remote systems:
- **User docs** — markdown files from a **GitLab** repository
- **Internal docs** — pages from a **Confluence** space
- **Tests** — issues from **Jira** via JQL

Requires the corresponding environment variables in `.env` (see below).

### 3. Connect your MCP client

The MCP server is available at `http://localhost:8080/mcp` (Streamable HTTP transport).

**VS Code Copilot** — already configured in `.vscode/mcp.json`.

**MCP Inspector** — for debugging:
```bash
npx @modelcontextprotocol/inspector
```
Then connect to `http://localhost:8080/mcp` with Streamable HTTP transport.

## Environment Variables

### Required (defaults provided)

| Variable | Default | Description |
|----------|---------|-------------|
| `CHROMA_HOST` | `chromadb` | ChromaDB hostname |
| `CHROMA_PORT` | `8000` | ChromaDB port |
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `mcp_qa` | Database name |
| `POSTGRES_USER` | `mcp_qa` | Database user |
| `POSTGRES_PASSWORD` | `mcp_qa` | Database password |

### GitLab (for `download-and-ingest` — user docs)

| Variable | Description |
|----------|-------------|
| `GITLAB_URL` | GitLab instance URL (e.g. `https://gitlab.com`) |
| `GITLAB_TOKEN` | Private access token |
| `GITLAB_PROJECT_ID` | Numeric project ID |
| `GITLAB_BRANCH` | Branch to read from (default: `main`) |
| `GITLAB_PATH` | Subdirectory to scope file search (optional) |

### Confluence (for `download-and-ingest` — internal docs)

| Variable | Description |
|----------|-------------|
| `CONFLUENCE_URL` | Confluence URL (e.g. `https://yourcompany.atlassian.net/wiki`) |
| `CONFLUENCE_EMAIL` | Atlassian account email |
| `CONFLUENCE_API_TOKEN` | Atlassian API token |
| `CONFLUENCE_SPACE_KEY` | Space key to fetch pages from |

### Jira (for `download-and-ingest` — tests)

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | Jira instance URL (e.g. `https://yourcompany.atlassian.net`) |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_API_TOKEN` | Atlassian API token |
| `JIRA_JQL` | JQL query to filter test issues (default: `labels = mcp`) |

## Stopping

```bash
docker compose down
```

To also remove orphan containers from previous configurations:

```bash
docker compose down --remove-orphans
```
