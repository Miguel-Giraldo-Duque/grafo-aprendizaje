"""Exporta nodos y relaciones a JSON y GraphML dentro de dumps/."""

from __future__ import annotations

import argparse
from pathlib import Path

from grafo_aprendizaje.config import load_settings
from grafo_aprendizaje.paths import assert_ignored_output, dumps_dir
from grafo_aprendizaje.serialize import dumps_json, graph_document, to_graphml
from grafo_aprendizaje.store import export_rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="grafo-exportar",
        description="Exporta el grafo a JSON y GraphML para inspeccionarlo sin restaurar la base.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Directorio de salida. Por defecto dumps/. Tiene que estar bajo dumps/ o data/.",
    )
    parser.add_argument(
        "--include-embeddings",
        action="store_true",
        help="Incluye los vectores. El archivo queda mucho más grande.",
    )
    args = parser.parse_args(argv)

    out_dir = args.out_dir if args.out_dir is not None else dumps_dir()
    out_dir = assert_ignored_output(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    settings = load_settings()
    nodes, relationships = export_rows(settings)
    document = graph_document(
        nodes,
        relationships,
        include_embeddings=args.include_embeddings,
    )
    json_path = out_dir / "grafo.json"
    graphml_path = out_dir / "grafo.graphml"
    json_path.write_text(dumps_json(document), encoding="utf-8")
    graphml_path.write_text(to_graphml(document), encoding="utf-8")
    print(f"Nodos: {len(document['nodes'])}")
    print(f"Relaciones: {len(document['relationships'])}")
    print(f"JSON: {json_path}")
    print(f"GraphML: {graphml_path}")


if __name__ == "__main__":
    main()
