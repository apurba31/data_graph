# Data Graph (minimal)

A minimal, runnable system aligned with `./.cursor/rules/agent.md`:

- **LangGraph orchestration**: a small ingestion graph
- **Neo4j in Docker**
- **Entity extraction pipeline**: simple rule-based extraction (offline + CI-friendly)
- **Graph builder using Cypher**
- **Example**: ingest a news article → build graph

## Quickstart

### Start Neo4j

```bash
docker compose -f docker-compose.neo4j.yml up -d
```

Neo4j will be available at:

- Browser UI: `http://localhost:7474`
- Bolt: `bolt://localhost:7687`

Default credentials (from `docker-compose.neo4j.yml`):

- user: `neo4j`
- password: `password`

### Install

```bash
python -m pip install -e ".[dev]"
```

### Run the example (news article → graph)

```bash
# Windows (PowerShell)
$env:NEO4J_URI="bolt://localhost:7687"
$env:NEO4J_USER="neo4j"
$env:NEO4J_PASSWORD="password"
python examples/ingest_news_article.py
```

If `NEO4J_URI` is not set, the pipeline runs in **dry-run** mode (it still builds Cypher, but skips writes).

## Tests

```bash
ruff check .
pytest -v
```

Integration test (requires Neo4j running + env vars set):

```bash
pytest -v -m integration
```

