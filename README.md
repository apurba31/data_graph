# Data Graph (minimal)

This repo is a **minimal, runnable “graph ingestion” system** aligned with `./.cursor/rules/agent.md`.

It demonstrates the core loop of a semantic/knowledge graph platform:

- **Ingest** unstructured text (a news article)
- **Extract** entities + lightweight relationships
- **Build** a graph model (nodes + edges + properties)
- **Persist** it into **Neo4j** using **parameterized Cypher**
- **Orchestrate** the workflow using **LangGraph**

The goal is to keep everything **simple, deterministic, and CI-friendly** (no LLM required) while still being an end-to-end runnable baseline you can extend.

## What this project is achieving

- **A working ingestion pipeline** you can run locally and in CI
- **A stable graph schema** you can query immediately in Neo4j
- **A starting point for a “Graph-Orchestrator” agent**: the code maps cleanly to the tasks described in `agent.md` (ingestion → extraction → Cypher → graph updates)

## What it wants to become (intended direction)

This is the seed of a larger platform where you can:

- ingest many sources (RSS/news, PDFs, internal docs)
- enrich with embeddings, entity linking, and better relationship extraction
- run graph queries (“who is connected to whom and why?”)
- track provenance and incremental updates over time

## Architecture (today)

### Components

- **Neo4j**: runs in Docker (`docker-compose.neo4j.yml`)
- **LangGraph**: orchestrates the ingestion steps as a small graph
- **Extractor**: rule-based entity/relationship extraction (offline)
- **Cypher builder**: converts extracted structure into parameterized Cypher

### Pipeline

`extract_entities` → `build_cypher` → `persist_neo4j`

### Graph schema

- `(:Article {id, title, text, ingested_at})`
- `(:Entity {name, type})`
- `(Article)-[:MENTIONS]->(Entity)`
- `(Entity)-[:RELATED_TO {kind}]->(Entity)`

## Repository layout

```
graph/ingestion/
  extract.py        # entity + relation extraction
  cypher.py         # parameterized Cypher statements
  neo4j_client.py   # Neo4j driver + batch persistence
  pipeline.py       # LangGraph orchestration + runner
examples/
  ingest_news_article.py
tests/
  test_article_ingestion.py
.github/workflows/
  ci.yml            # ruff + pytest + Neo4j service in CI
```

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

### Verify in Neo4j Browser

Open `http://localhost:7474` (user `neo4j`, password `password`) and run:

```cypher
MATCH (a:Article)-[:MENTIONS]->(e:Entity)
RETURN a.id, a.title, collect(distinct e.name) AS entities;
```

```cypher
MATCH (e:Entity)-[r:RELATED_TO]->(f:Entity)
RETURN e.name AS source, f.name AS target, r.kind AS kind
LIMIT 25;
```

## Tests

```bash
ruff check .
pytest -v
```

Integration test (requires Neo4j running + env vars set):

```bash
pytest -v -m integration
```

## Current limitations (by design)

- **Entity extraction is heuristic** (capitalization + a small known-org list). It’s meant to be a placeholder that is easy to understand and test.
- **Relationships are co-occurrence** within a sentence (`RELATED_TO`). This is a demo relationship, not a semantic claim.
- **No dedup/linking beyond case-insensitive name matching**.

## Next steps (good extensions)

- Replace the extractor with an **LLM-based structured extractor** (or spaCy) while keeping tests via golden fixtures.
- Add **entity linking** (canonical IDs), not just names.
- Add **provenance** on relationships (source sentence offsets, confidence, source URL).
- Add **embeddings** + a semantic retrieval layer (hybrid: vector + graph).

