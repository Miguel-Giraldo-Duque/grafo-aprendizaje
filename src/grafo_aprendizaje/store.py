"""Lecturas Neo4j para pasajes, vecinos y la exportación."""

from __future__ import annotations

from typing import Any

from grafo_aprendizaje import cypher
from grafo_aprendizaje.config import Settings
from grafo_aprendizaje.textutil import SNIPPET_CHARS, PASSAGE_CHARS


def read(settings: Settings, query: str, **params: Any) -> list[dict[str, Any]]:
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(settings.uri, auth=(settings.user, settings.password))
    try:
        driver.verify_connectivity()
        with driver.session(database=settings.database) as session:
            return [record.data() for record in session.run(query, **params)]
    finally:
        driver.close()


def sources_for(settings: Settings, chunk_ids: list[str]) -> dict[str, tuple[str | None, int | None]]:
    if not chunk_ids:
        return {}
    rows = read(settings, cypher.SOURCES_BY_CHUNK, ids=chunk_ids)
    found: dict[str, tuple[str | None, int | None]] = {}
    for row in rows:
        page = row.get("page")
        found[row["chunk_id"]] = (row.get("source"), None if page is None else int(page))
    return found


def chunk_exists(settings: Settings, chunk_id: str) -> bool:
    return bool(read(settings, cypher.CHUNK_EXISTS, chunk_id=chunk_id))


def page_chunks(settings: Settings, source: str, page: int) -> list[dict[str, Any]]:
    return read(settings, cypher.PAGE_CHUNKS, source=source, page=page)


def neighbors(settings: Settings, chunk_id: str, limit: int) -> dict[str, Any] | None:
    rows = read(
        settings,
        cypher.NEIGHBORS,
        chunk_id=chunk_id,
        limit=limit,
        snippet=SNIPPET_CHARS,
        passage=PASSAGE_CHARS,
    )
    return rows[0] if rows else None


def export_rows(settings: Settings) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = read(settings, cypher.EXPORT_NODES)
    relationships = read(settings, cypher.EXPORT_RELATIONSHIPS)
    return nodes, relationships
