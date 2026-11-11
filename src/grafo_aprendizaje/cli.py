"""CLI: ingiere un archivo local con ungraph.ingest_document."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from grafo_aprendizaje.config import configure_ungraph, load_settings
from grafo_aprendizaje.textutil import ensure_supported, ingest_report


def usage() -> str:
    return """Grafo de aprendizaje

  uv run grafo-ingerir ARCHIVO
      Ingesta Markdown, TXT, Word o PDF al grafo File → Page → Chunk.

  uv run grafo-mcp
      Servidor FastMCP por stdio (search, get_passage, related).

  uv run python -m grafo_aprendizaje.mcp_server
      El mismo servidor, como módulo.

  uv run grafo-exportar
      Exporta nodos y relaciones a dumps/grafo.json y dumps/grafo.graphml.

  ./scripts/neo4j-dump.sh
  ./scripts/neo4j-load.sh
      Copia y restauración con neo4j-admin database dump / load.
"""


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="grafo-ingerir",
        description="Ingesta un archivo local al grafo léxico con ungraph 0.1.5.",
    )
    parser.add_argument("archivo", type=Path, help="Ruta local. No tiene que estar en el repo.")
    parser.add_argument("--chunk-size", type=int, default=1000)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(levelname)s %(message)s")
    path = args.archivo.expanduser().resolve()
    ensure_supported(path)

    import ungraph

    settings = load_settings()
    configure_ungraph(settings)
    chunks = ungraph.ingest_document(
        path,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )
    print(ingest_report(path, chunks))


if __name__ == "__main__":
    main()
