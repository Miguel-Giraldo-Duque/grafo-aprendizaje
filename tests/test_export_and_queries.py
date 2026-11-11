import ast
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from grafo_aprendizaje import cypher
from grafo_aprendizaje.paths import assert_ignored_output, repo_root
from grafo_aprendizaje.serialize import graph_document, to_graphml

ROOT = repo_root()


def test_cypher_uses_the_ungraph_lexical_pattern():
    blob = "\n".join(
        [
            cypher.SOURCES_BY_CHUNK,
            cypher.PAGE_CHUNKS,
            cypher.NEIGHBORS,
            cypher.EXPORT_NODES,
            cypher.EXPORT_RELATIONSHIPS,
        ]
    )
    for token in ("File", "Page", "Chunk", "CONTAINS", "HAS_CHUNK", "NEXT_CHUNK", "page_content"):
        assert token in blob


def test_graphml_is_xml_and_omits_vectors():
    document = graph_document(
        [
            {
                "id": "4:abc:1",
                "labels": ["Chunk"],
                "props": {"page_content": "hola <mundo>\x00", "embeddings": [0.2] * 32},
            }
        ],
        [
            {
                "id": "5:abc:9",
                "type": "NEXT_CHUNK",
                "start": "4:abc:1",
                "end": "4:abc:1",
                "props": {},
            }
        ],
        include_embeddings=False,
    )
    xml = to_graphml(document)
    root = ET.fromstring(xml)
    assert root.tag.endswith("graphml")
    assert "hola" in xml
    assert "0.2, 0.2" not in xml
    assert "&lt;mundo&gt;" in xml


def test_export_refuses_paths_outside_ignored_dirs(tmp_path: Path):
    dumped = assert_ignored_output(ROOT / "dumps" / "revisar")
    assert dumped == (ROOT / "dumps" / "revisar").resolve()
    try:
        assert_ignored_output(tmp_path / "grafo.json")
    except SystemExit as exc:
        assert "dumps/" in str(exc)
    else:
        raise AssertionError("debía rechazar una ruta fuera de dumps/ y data/")


def test_mcp_exposes_only_the_three_tools():
    source = (ROOT / "src" / "grafo_aprendizaje" / "mcp_server.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    tools = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            name = ""
            if isinstance(deco, ast.Attribute):
                name = deco.attr
            elif isinstance(deco, ast.Name):
                name = deco.id
            if name == "tool":
                tools.append(node.name)
    assert tools == ["search", "get_passage", "related"]


def test_gitignore_blocks_data_dumps_secrets_and_books():
    samples = [
        "data/neo4j/databases/neo4j/neostore",
        "dumps/neo4j.dump",
        "dumps/grafo.graphml",
        "volumes/neo4j/data",
        ".env",
        "libros/algo.pdf",
        "notas-sueltas.pdf",
        "corpus/capitulo.docx",
        ".cache/huggingface/model.bin",
    ]
    result = subprocess.run(
        ["git", "check-ignore", "-v", *samples],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    ignored = {line.split()[-1] for line in result.stdout.splitlines()}
    assert ignored == set(samples)

    example = subprocess.run(
        ["git", "check-ignore", "-v", ".env.example"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert "!.env.example" in example.stdout

    visible = subprocess.run(
        ["git", "check-ignore", "README.md", "src/grafo_aprendizaje/cli.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert visible.returncode == 1
    assert visible.stdout == ""
