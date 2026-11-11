"""Formato de confirmaciones, pasajes y propiedades, sin I/O."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt", ".doc", ".docx", ".pdf"}
PASSAGE_CHARS = 500
SNIPPET_CHARS = 280
EMBEDDING_KEYS = {"embeddings", "embedding"}


def ensure_supported(path: Path) -> None:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        accepted = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise SystemExit(
            f"Extensión {suffix or '(sin extensión)'} no la acepta ungraph 0.1.5. "
            f"Usa: {accepted}."
        )
    if not path.is_file():
        raise SystemExit(f"No encuentro el archivo: {path}")


def page_of(chunk: Any) -> int:
    number = None
    getter = getattr(chunk, "get_page_number", None)
    if callable(getter):
        number = getter()
    if number is None:
        metadata = getattr(chunk, "metadata", None) or {}
        number = metadata.get("page_number")
    if number is None:
        return 1
    return int(number)


def filename_of(chunk: Any, fallback: str) -> str:
    getter = getattr(chunk, "get_filename", None)
    if callable(getter):
        name = getter()
        if name:
            return str(name)
    metadata = getattr(chunk, "metadata", None) or {}
    return str(metadata.get("filename") or fallback)


def title_of(path: Path, chunks: Sequence[Any]) -> str:
    if chunks:
        metadata = getattr(chunks[0], "metadata", None) or {}
        for key in ("title", "Title"):
            if metadata.get(key):
                return str(metadata[key])
    return path.stem


def format_pages(pages: Sequence[int]) -> str:
    unique = sorted(set(pages))
    if not unique:
        return "0"
    if len(unique) <= 8:
        numbers = ", ".join(str(number) for number in unique)
        return f"{len(unique)} ({numbers})"
    return f"{len(unique)} ({unique[0]}–{unique[-1]})"


def ingest_report(path: Path, chunks: Sequence[Any]) -> str:
    pages = [page_of(chunk) for chunk in chunks]
    filename = filename_of(chunks[0], path.name) if chunks else path.name
    lines = [
        f"Título: {title_of(path, chunks)}",
        f"Archivo: {filename}",
        f"Páginas: {format_pages(pages)}",
        f"Chunks: {len(chunks)}",
    ]
    return "\n".join(lines)


def shorten(text: str | None, limit: int = PASSAGE_CHARS) -> str:
    value = text or ""
    if len(value) <= limit:
        return value
    return value[:limit].rstrip() + "…"


def shape_hit(
    *,
    content: str | None,
    score: float | None,
    chunk_id: str | None,
    consecutive: int | None,
    source: str | None,
    page: int | None,
) -> dict[str, Any]:
    return {
        "source": source,
        "page": page,
        "chunk_id": chunk_id,
        "chunk_id_consecutive": consecutive,
        "score": None if score is None else round(float(score), 4),
        "passage": shorten(content, PASSAGE_CHARS),
    }


def assemble_page(source: str, page: int, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row.get("n") is None, row.get("n") or 0))
    chunks = [
        {
            "chunk_id": row.get("chunk_id"),
            "n": row.get("n"),
            "text": row.get("content") or "",
        }
        for row in ordered
    ]
    return {
        "source": source,
        "page": page,
        "found": bool(chunks),
        "text": "\n".join(chunk["text"] for chunk in chunks),
        "chunks": chunks,
    }


def is_embedding_value(value: Any) -> bool:
    if not isinstance(value, list) or len(value) <= 16:
        return False
    sample = value[:8]
    return all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in sample)


def public_properties(props: Mapping[str, Any] | None, *, include_embeddings: bool) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in (props or {}).items():
        if not include_embeddings and (key in EMBEDDING_KEYS or is_embedding_value(value)):
            length = len(value) if isinstance(value, list) else None
            cleaned[key] = {"omitted": True, "length": length}
            continue
        cleaned[key] = _jsonable(value)
    return cleaned


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)
