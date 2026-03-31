from __future__ import annotations

import uuid
from typing import Any

from langgraph.graph import END, StateGraph

from graph.ingestion.cypher import build_cypher_batch
from graph.ingestion.extract import extract_entities_and_relations
from graph.ingestion.neo4j_client import get_neo4j_driver, persist_batch
from graph.ingestion.state import ArticleIngestionState


def _extract_node(state: ArticleIngestionState) -> dict[str, Any]:
    text = state.get("text", "")
    try:
        entities, relationships = extract_entities_and_relations(text)
        return {"entities": entities, "relationships": relationships, "error": None}
    except Exception as exc:  # noqa: BLE001 — surface any extraction bug as state error
        return {"entities": [], "relationships": [], "error": str(exc)}


def _cypher_node(state: ArticleIngestionState) -> dict[str, Any]:
    if state.get("error"):
        return {}
    article_id = state.get("article_id") or uuid.uuid4().hex
    title = state.get("title") or "Untitled"
    text = state.get("text", "")
    entities = state.get("entities") or []
    relationships = state.get("relationships") or []
    stmts = build_cypher_batch(article_id, title, text, entities, relationships)
    return {
        "article_id": article_id,
        "cypher_statements": stmts,
    }


def _persist_node(state: ArticleIngestionState) -> dict[str, Any]:
    if state.get("error"):
        return {"neo4j_summary": {"skipped": True, "reason": "prior_error"}}
    stmts = state.get("cypher_statements") or []
    driver = get_neo4j_driver()
    try:
        summary = persist_batch(driver, stmts)
        return {"neo4j_summary": summary}
    finally:
        if driver is not None:
            driver.close()


def build_article_ingestion_graph():
    """LangGraph: extract → build Cypher → persist to Neo4j."""
    g = StateGraph(ArticleIngestionState)
    g.add_node("extract_entities", _extract_node)
    g.add_node("build_cypher", _cypher_node)
    g.add_node("persist_neo4j", _persist_node)
    g.set_entry_point("extract_entities")
    g.add_edge("extract_entities", "build_cypher")
    g.add_edge("build_cypher", "persist_neo4j")
    g.add_edge("persist_neo4j", END)
    return g.compile()


def run_article_ingestion(
    text: str,
    *,
    article_id: str | None = None,
    title: str | None = None,
) -> ArticleIngestionState:
    """Run the full graph and return final state."""
    graph = build_article_ingestion_graph()
    initial: ArticleIngestionState = {
        "article_id": article_id or "",
        "title": title or "",
        "text": text,
        "entities": [],
        "relationships": [],
        "cypher_statements": [],
        "neo4j_summary": {},
        "error": None,
    }
    result = graph.invoke(initial)
    return result  # type: ignore[return-value]

