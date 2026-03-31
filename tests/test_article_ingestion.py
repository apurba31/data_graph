from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from graph.ingestion.cypher import build_cypher_batch
from graph.ingestion.extract import extract_entities_and_relations
from graph.ingestion.neo4j_client import persist_batch, run_cypher_batch
from graph.ingestion.pipeline import build_article_ingestion_graph, run_article_ingestion


class TestExtract:
    def test_finds_multi_word_and_org_hints(self) -> None:
        text = "OpenAI met with Microsoft leaders. Google stayed quiet."
        entities, rels = extract_entities_and_relations(text)
        names = {e["name"] for e in entities}
        assert "OpenAI" in names
        assert "Microsoft" in names
        assert "Google" in names
        assert rels  # co-occurrence in same sentence

    def test_empty_text(self) -> None:
        assert extract_entities_and_relations("") == ([], [])


class TestCypher:
    def test_build_batch_has_article_and_entities(self) -> None:
        entities = [{"name": "OpenAI", "type": "ORG"}]
        rels: list[dict] = []
        batch = build_cypher_batch("aid", "T", "body", entities, rels)
        assert batch
        first = batch[0][0]
        assert "Article" in first
        assert "MERGE" in first


class TestPipeline:
    def test_graph_compiles(self) -> None:
        g = build_article_ingestion_graph()
        assert g is not None

    def test_run_without_neo4j_dry_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("NEO4J_URI", raising=False)
        state = run_article_ingestion("Apple and Microsoft issued statements.", title="t")
        assert state.get("neo4j_summary", {}).get("dry_run") is True

    def test_run_with_mock_driver(self) -> None:
        mock_driver = MagicMock()
        mock_session = MagicMock()

        def exec_write(work_fn):
            tx = MagicMock()
            return work_fn(tx)

        mock_session.execute_write.side_effect = exec_write
        mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

        with patch("graph.ingestion.pipeline.get_neo4j_driver", return_value=mock_driver):
            state = run_article_ingestion("OpenAI and Google compete.", title="x", article_id="a1")

        assert state.get("neo4j_summary", {}).get("dry_run") is False
        mock_driver.close.assert_called_once()


class TestNeo4jClient:
    def test_run_cypher_batch_invokes_transaction(self) -> None:
        driver = MagicMock()
        session = MagicMock()
        driver.session.return_value.__enter__ = MagicMock(return_value=session)
        driver.session.return_value.__exit__ = MagicMock(return_value=False)

        def exec_write(work_fn):
            tx = MagicMock()
            return work_fn(tx)

        session.execute_write.side_effect = exec_write

        stmts = [
            ("RETURN 1 AS n", {}),
            ("RETURN 2 AS n", {}),
        ]
        out = run_cypher_batch(driver, stmts)  # type: ignore[arg-type]
        assert out["statements"] == 2
        session.execute_write.assert_called_once()

    def test_persist_batch_no_driver(self) -> None:
        out = persist_batch(None, [("RETURN 1", {})])
        assert out["dry_run"] is True


@pytest.mark.integration
def test_full_pipeline_against_neo4j() -> None:
    uri = os.environ.get("NEO4J_URI", "").strip()
    if not uri:
        pytest.skip("NEO4J_URI not set (local run without Neo4j)")

    os.environ.setdefault("NEO4J_USER", "neo4j")
    if not os.environ.get("NEO4J_PASSWORD"):
        pytest.skip("NEO4J_PASSWORD not set (needed with NEO4J_URI for integration)")

    state = run_article_ingestion(
        "OpenAI and Microsoft announced a partnership. Google was not present.",
        title="Integration article",
        article_id="pytest-integration-001",
    )
    assert not state.get("error")
    summary = state.get("neo4j_summary") or {}
    assert summary.get("dry_run") is False
    assert summary.get("statements", 0) > 0

