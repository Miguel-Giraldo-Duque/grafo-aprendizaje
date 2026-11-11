"""Servidor FastMCP en stdio para que un agente consulte el grafo.

Arranque:
  uv run grafo-mcp
  uv run python -m grafo_aprendizaje.mcp_server

FastMCP 4.1.8: FastMCP(...), @mcp.tool y run(transport="stdio").
El transporte por defecto ya es stdio; aquí se fija para el conector.
"""

from __future__ import annotations

import os

# La primera búsqueda descarga el modelo. Estas variables evitan barras
# de progreso que FastMCP no quiere ver mezcladas con el protocolo.
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

from fastmcp import FastMCP

mcp = FastMCP(
    name="grafo-aprendizaje",
    instructions=(
        "Grafo léxico personal en Neo4j (File -CONTAINS-> Page -HAS_CHUNK-> Chunk, "
        "y Chunk -NEXT_CHUNK-> Chunk), construido con ungraph. "
        "search devuelve extractos cortos con archivo y página. "
        "get_passage devuelve el texto guardado de una página. "
        "related devuelve los nodos vecinos de un chunk_id o de una idea. "
        "El archivo fuente es el nombre del fichero (notas.md), no la ruta completa."
    ),
)


@mcp.tool
def search(query: str, limit: int = 5, mode: str = "hybrid") -> list[dict]:
    """Busca pasajes cortos en el grafo.

    mode es "hybrid" (texto y vector, el de ungraph.hybrid_search),
    "vector" (ungraph.vector_search) o "text" (ungraph.search).
    Cada resultado trae source, page, chunk_id, score y passage.
    """
    from grafo_aprendizaje.retrieval import search_passages

    return search_passages(query=query, limit=limit, mode=mode)


@mcp.tool
def get_passage(source: str, page: int) -> dict:
    """Devuelve el texto guardado de una página.

    source es el nombre de archivo que ungraph usó como File.filename.
    page es Page.page_number (entero, desde 1).
    El texto es la concatenación de los Chunk de esa página, en orden
    chunk_id_consecutive. El solapamiento de chunks puede repetir frases.
    """
    from grafo_aprendizaje.retrieval import get_passage as fetch_passage

    return fetch_passage(source=source, page=page)


@mcp.tool
def related(ref: str, limit: int = 12) -> dict:
    """Devuelve los vecinos de un chunk o de una idea.

    ref puede ser un chunk_id. Si no existe ese nodo, se toma como idea
    y se resuelve con ungraph.hybrid_search (y vector_search si no hay
    intersección). No incluye los vectores de embeddings.
    """
    from grafo_aprendizaje.retrieval import related as fetch_related

    return fetch_related(ref=ref, limit=limit)


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
