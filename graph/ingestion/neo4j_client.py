from __future__ import annotations

import os
from typing import Any

from neo4j import Driver, GraphDatabase


def get_neo4j_driver() -> Driver | None:
    """Return a Neo4j driver from env, or None if URI is unset (unit tests / dry-run)."""
    uri = os.environ.get("NEO4J_URI", "").strip()
    if not uri:
        return None
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))


def run_cypher_batch(
    driver: Driver,
    statements: list[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Execute all statements in one write transaction."""

    def work(tx: Any) -> int:
        n = 0
        for stmt, params in statements:
            tx.run(stmt, params)
            n += 1
        return n

    with driver.session() as session:
        n = session.execute_write(work)
    return {"statements": n, "errors": 0}


def persist_batch(
    driver: Driver | None,
    statements: list[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Run batch if driver is available; otherwise return a dry-run summary."""
    if driver is None:
        return {"dry_run": True, "would_run": len(statements)}
    summary = run_cypher_batch(driver, statements)
    summary["dry_run"] = False
    return summary

