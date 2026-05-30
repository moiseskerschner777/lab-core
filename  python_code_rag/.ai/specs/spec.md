# spec.md — python-code-rag

## What

A FastAPI service that indexes Python codebases into IRIS Vector Search and exposes a semantic search API. Each indexed directory becomes its own isolated namespace in IRIS. External tools (MCP servers, Cursor, etc.) connect via HTTP to search code semantically and list available collections.

## Why

Large codebases are hard to navigate mentally. This service gives any MCP-compatible tool the ability to ask "where is authentication handled?" or "which functions touch the database?" and get back ranked, grounded code chunks — without reading every file.

## Users

A developer running the stack locally. The `python_code_rag` stack is standalone for development — it connects to the existing IRIS instance via `lab-core_default` Docker network. Later it will be merged into the root `docker-compose.yml`.

## Capabilities

- **Index**: receive a directory path (mounted into the container), parse every `.py` file with tree-sitter, extract function / class / module / import chunks, embed with Ollama, store vectors in IRIS.
- **Search**: receive a query string + collection name, return ranked code chunks with file, line, type, name, and score.
- **List collections**: return all indexed collections currently in IRIS.
- **Health check**: confirm the service, IRIS, and Ollama are reachable.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/index` | Index a directory path into its own collection |
| POST | `/search` | Semantic search within a collection |
| GET | `/collections` | List all available collections |
| GET | `/health` | Service + dependency health check |

## Constraints

- Standalone `docker-compose.yml` inside `python_code_rag/` — no changes to root compose during development.
- Connects to existing IRIS instance via external Docker network `lab-core_default`.
- Ollama runs as a local service in this compose with NVIDIA GPU passthrough (RTX 5080).
- Python codebase only (tree-sitter Python grammar).
- Codebases mounted into the container as volumes — paths resolved inside the container.
- No authentication on the API (local use only).
- App exposed on port **8001** (port 8000 already used by `labcore`).

## Out of scope

- Multi-language support
- Authentication / API keys
- Chat / LLM response generation (the calling MCP handles that)
- Web UI
- Streaming responses
- Root docker-compose.yml integration (Phase 6 / future)
