from __future__ import annotations

from typing import Any


def build_cypher_batch(
    article_id: str,
    title: str,
    text: str,
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> list[tuple[str, dict[str, Any]]]:
    """Build parameterized Cypher statements (statement, params) for one transaction.

    Schema:
      (:Article {id, title, text})
      (:Entity {name, type})
      (Article)-[:MENTIONS]->(Entity)
      (Entity)-[:RELATED_TO]->(Entity)
    """
    stmts: list[tuple[str, dict[str, Any]]] = []

    stmts.append(
        (
            (
                "MERGE (a:Article {id: $article_id}) "
                "SET a.title = $title, a.text = $text, a.ingested_at = datetime()"
            ),
            {
                "article_id": article_id,
                "title": title,
                "text": text,
            },
        )
    )

    for ent in entities:
        stmts.append(
            (
                (
                    "MERGE (e:Entity {name: $name, type: $etype}) "
                    "WITH e MATCH (a:Article {id: $article_id}) "
                    "MERGE (a)-[:MENTIONS]->(e)"
                ),
                {
                    "name": ent["name"],
                    "etype": ent["type"],
                    "article_id": article_id,
                },
            )
        )

    for rel in relationships:
        stmts.append(
            (
                (
                    "MATCH (s:Entity {name: $sname}), (t:Entity {name: $tname}) "
                    "MERGE (s)-[:RELATED_TO {kind: $rtype}]->(t)"
                ),
                {
                    "sname": rel["source"],
                    "tname": rel["target"],
                    "rtype": rel["type"],
                },
            )
        )

    return stmts

