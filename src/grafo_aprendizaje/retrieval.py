"""Búsqueda y navegación usando la API pública de ungraph 0.1.5."""

from __future__ import annotations

from typing import Any

from grafo_aprendizaje.config import configure_ungraph, load_settings
from grafo_aprendizaje.store import chunk_exists, neighbors, page_chunks, sources_for
from grafo_aprendizaje.textutil import assemble_page, shape_hit, shorten

MODES = ("hybrid", "vector", "text")
MAX_RESULTS = 20


def search_passages(query: str, limit: int = 5, mode: str = "hybrid") -> list[dict[str, Any]]:
    text = query.strip()
    if not text:
        raise ValueError("La consulta está vacía.")
    if mode not in MODES:
        raise ValueError("mode debe ser hybrid, vector o text.")
    capped = max(1, min(int(limit), MAX_RESULTS))

    import ungraph

    settings = load_settings()
    configure_ungraph(settings)
    hits = _search(ungraph, text, capped, mode)
    located = sources_for(settings, [hit.chunk_id for hit in hits if hit.chunk_id])
    passages = []
    for hit in hits:
        source, page = located.get(hit.chunk_id, (None, None))
        passages.append(
            shape_hit(
                content=hit.content,
                score=hit.score,
                chunk_id=hit.chunk_id,
                consecutive=hit.chunk_id_consecutive,
                source=source,
                page=page,
            )
        )
    return passages


def get_passage(source: str, page: int) -> dict[str, Any]:
    name = source.strip()
    if not name:
        raise ValueError("Falta el archivo fuente. Usa el nombre, por ejemplo notas.md.")
    page_number = int(page)
    if page_number < 1:
        raise ValueError("La página debe ser un entero mayor o igual que 1.")
    settings = load_settings()
    rows = page_chunks(settings, name, page_number)
    return assemble_page(name, page_number, rows)


def related(ref: str, limit: int = 12) -> dict[str, Any]:
    token = ref.strip()
    if not token:
        raise ValueError("Indica un chunk_id o una idea corta.")
    capped = max(1, min(int(limit), 50))
    settings = load_settings()
    chunk_id, via = _resolve_chunk(settings, token)
    if not chunk_id:
        return {
            "ref": token,
            "found": False,
            "resolved_via": None,
            "chunk_id": None,
            "neighbors": [],
        }
    row = neighbors(settings, chunk_id, capped) or {}
    content = row.get("content")
    return {
        "ref": token,
        "found": True,
        "resolved_via": via,
        "chunk_id": chunk_id,
        "source": row.get("source"),
        "page": None if row.get("page") is None else int(row["page"]),
        "passage": shorten(content),
        "neighbors": list(row.get("neighbors") or []),
    }


def _resolve_chunk(settings: Any, ref: str) -> tuple[str | None, str | None]:
    if chunk_exists(settings, ref):
        return ref, "chunk_id"
    import ungraph

    configure_ungraph(settings)
    hits = ungraph.hybrid_search(ref, limit=1)
    if not hits:
        hits = ungraph.vector_search(ref, limit=1)
    if not hits:
        return None, None
    return hits[0].chunk_id, "idea"


def _search(ungraph: Any, query: str, limit: int, mode: str) -> list[Any]:
    if mode == "vector":
        return ungraph.vector_search(query, limit=limit)
    if mode == "text":
        return ungraph.search(query, limit=limit)
    return ungraph.hybrid_search(query, limit=limit)
