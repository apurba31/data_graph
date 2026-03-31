from __future__ import annotations

import re
from typing import Any

# Common sentence-start words to skip as false-positive "entities"
_STOP = frozenset(
    {
        "The",
        "A",
        "An",
        "This",
        "That",
        "These",
        "Those",
        "There",
        "Here",
        "When",
        "Where",
        "What",
        "Which",
        "Who",
        "How",
        "If",
        "In",
        "On",
        "At",
        "By",
        "For",
        "As",
        "But",
        "And",
        "Or",
        "Not",
        "No",
        "Yes",
        "All",
        "Some",
        "Many",
        "Most",
        "Such",
        "Other",
        "Another",
        "Each",
        "Every",
        "Both",
        "Several",
        "Few",
    }
)

# Hint list for ORG vs PERSON heuristics (minimal demo set)
_KNOWN_ORGS = frozenset(
    {
        "Apple",
        "Microsoft",
        "Google",
        "OpenAI",
        "Amazon",
        "Meta",
        "Tesla",
        "EU",
        "NATO",
        "UN",
        "Reuters",
        "Bloomberg",
    }
)

_MULTI_WORD = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
)
_SINGLE_CAP = re.compile(r"\b([A-Z][a-z]{2,})\b")


def _classify(name: str) -> str:
    first = name.split()[0]
    if name in _KNOWN_ORGS or first in _KNOWN_ORGS:
        return "ORG"
    if len(name.split()) >= 2:
        return "PERSON"
    return "MISC"


def _normalize_entities(raw: set[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name in sorted(raw, key=len, reverse=True):
        trimmed = name.strip()
        if not trimmed or trimmed in _STOP:
            continue
        key = trimmed.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": trimmed, "type": _classify(trimmed)})
    return out


def extract_entities_and_relations(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Rule-based extraction: capitalized phrases + co-occurrence within a sentence.

    No external ML — keeps the demo runnable offline and CI-friendly.
    """
    if not text or not text.strip():
        return [], []

    raw: set[str] = set()
    for m in _MULTI_WORD.finditer(text):
        raw.add(m.group(1))
    for m in _SINGLE_CAP.finditer(text):
        word = m.group(1)
        if word not in _STOP:
            raw.add(word)

    # CamelCase brands (e.g. OpenAI) that do not match the Title Case word patterns
    for org in _KNOWN_ORGS:
        if org in text:
            raw.add(org)

    entities = _normalize_entities(raw)

    relationships: list[dict[str, Any]] = []

    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        in_sentence: list[str] = []
        for e in entities:
            if e["name"] in sent:
                in_sentence.append(e["name"])
        for i, a in enumerate(in_sentence):
            for b in in_sentence[i + 1 :]:
                if a != b:
                    relationships.append(
                        {
                            "source": a,
                            "target": b,
                            "type": "RELATED_TO",
                        }
                    )

    return entities, relationships

