"""Example: ingest a short news-style article into Neo4j via LangGraph.

Prerequisites:
  docker compose -f docker-compose.neo4j.yml up -d
  python -m pip install -e ".[dev]"

Then (PowerShell):
  $env:NEO4J_URI="bolt://localhost:7687"
  $env:NEO4J_USER="neo4j"
  $env:NEO4J_PASSWORD="password"
  python examples/ingest_news_article.py
"""

from __future__ import annotations

import os

from graph.ingestion import run_article_ingestion

SAMPLE_ARTICLE = """
OpenAI unveiled a new system today in San Francisco. Microsoft said it would
integrate similar capabilities across its products. Google and Meta are expected
to respond within weeks, according to analysts at Reuters.
"""


def main() -> None:
    os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
    os.environ.setdefault("NEO4J_USER", "neo4j")
    os.environ.setdefault("NEO4J_PASSWORD", "password")

    state = run_article_ingestion(
        SAMPLE_ARTICLE.strip(),
        title="Big Tech responds to new AI launch",
        article_id="news-demo-001",
    )
    print("article_id:", state.get("article_id"))
    print("entities:", len(state.get("entities") or []))
    print("relationships:", len(state.get("relationships") or []))
    print("cypher statements:", len(state.get("cypher_statements") or []))
    print("neo4j_summary:", state.get("neo4j_summary"))
    if state.get("error"):
        print("error:", state["error"])


if __name__ == "__main__":
    main()

