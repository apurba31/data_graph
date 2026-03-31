from __future__ import annotations

from typing import Any, TypedDict


class ArticleIngestionState(TypedDict, total=False):
    """State for LangGraph article → Neo4j pipeline.

    Flow: extract_entities → build_cypher → persist_neo4j → END
    """

    article_id: str
    title: str
    text: str
    entities: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    cypher_statements: list[tuple[str, dict[str, Any]]]
    neo4j_summary: dict[str, Any]
    error: str | None

