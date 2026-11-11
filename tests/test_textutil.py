from pathlib import Path

from grafo_aprendizaje.textutil import (
    assemble_page,
    format_pages,
    ingest_report,
    page_of,
    public_properties,
    shape_hit,
    shorten,
)


class _Chunk:
    def __init__(self, filename, page, title=None):
        self.metadata = {"filename": filename, "page_number": page}
        if title:
            self.metadata["title"] = title

    def get_filename(self):
        return self.metadata["filename"]

    def get_page_number(self):
        return self.metadata["page_number"]


def test_ingest_report_lists_title_pages_and_chunks():
    chunks = [_Chunk("notas.md", 1, title="Notas de campo"), _Chunk("notas.md", 1), _Chunk("notas.md", 2)]
    report = ingest_report(Path("/tmp/notas.md"), chunks)
    assert "Título: Notas de campo" in report
    assert "Archivo: notas.md" in report
    assert "Páginas: 2 (1, 2)" in report
    assert "Chunks: 3" in report


def test_page_defaults_to_one_when_metadata_has_none():
    class Bare:
        metadata = {}

        def get_page_number(self):
            return None

    assert page_of(Bare()) == 1
    assert format_pages([1, 1, 1]) == "1 (1)"


def test_shape_hit_shortens_and_keeps_source():
    long = "a" * 600
    hit = shape_hit(
        content=long,
        score=0.123456,
        chunk_id="c1",
        consecutive=3,
        source="notas.md",
        page=4,
    )
    assert hit["source"] == "notas.md"
    assert hit["page"] == 4
    assert hit["score"] == 0.1235
    assert hit["passage"].endswith("…")
    assert len(hit["passage"]) < len(long)
    assert shorten("hola") == "hola"


def test_assemble_page_orders_chunks_and_marks_missing():
    empty = assemble_page("notas.md", 2, [])
    assert empty["found"] is False
    assert empty["text"] == ""

    page = assemble_page(
        "notas.md",
        2,
        [
            {"chunk_id": "b", "n": 2, "content": "segundo"},
            {"chunk_id": "a", "n": 1, "content": "primero"},
        ],
    )
    assert page["found"] is True
    assert page["text"] == "primero\nsegundo"
    assert [chunk["chunk_id"] for chunk in page["chunks"]] == ["a", "b"]


def test_public_properties_drop_embedding_vectors():
    props = public_properties(
        {"page_content": "hola", "embeddings": [0.1] * 384, "page_number": 2},
        include_embeddings=False,
    )
    assert props["page_content"] == "hola"
    assert props["embeddings"]["omitted"] is True
    assert props["embeddings"]["length"] == 384

    kept = public_properties({"embeddings": [0.1, 0.2]}, include_embeddings=True)
    assert kept["embeddings"] == [0.1, 0.2]
