"""Exportación JSON y GraphML para inspeccionar el grafo sin restaurar la base."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from typing import Any, Mapping
from xml.sax.saxutils import escape

from grafo_aprendizaje.textutil import public_properties

# XML 1.0 no admite estos controles; el texto de un PDF a veces los trae.
_INVALID_XML = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")

GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"


def graph_document(
    nodes: list[Mapping[str, Any]],
    relationships: list[Mapping[str, Any]],
    *,
    include_embeddings: bool,
) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": node["id"],
                "labels": list(node.get("labels") or []),
                "properties": public_properties(node.get("props"), include_embeddings=include_embeddings),
            }
            for node in nodes
        ],
        "relationships": [
            {
                "id": rel["id"],
                "type": rel["type"],
                "start": rel["start"],
                "end": rel["end"],
                "properties": public_properties(rel.get("props"), include_embeddings=include_embeddings),
            }
            for rel in relationships
        ],
    }


def dumps_json(document: Mapping[str, Any]) -> str:
    return json.dumps(document, ensure_ascii=False, indent=2)


def to_graphml(document: Mapping[str, Any]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<graphml xmlns="{GRAPHML_NS}">',
        '  <key id="labels" for="node" attr.name="labels" attr.type="string"/>',
        '  <key id="props" for="node" attr.name="properties" attr.type="string"/>',
        '  <key id="type" for="edge" attr.name="type" attr.type="string"/>',
        '  <key id="eprops" for="edge" attr.name="properties" attr.type="string"/>',
        '  <graph id="grafo" edgedefault="directed">',
    ]
    for node in document["nodes"]:
        node_id = _xml_id("n", node["id"])
        labels = ",".join(node["labels"])
        props = _xml_text(json.dumps(node["properties"], ensure_ascii=False))
        lines.append(f'    <node id="{node_id}">')
        lines.append(f"      <data key=\"labels\">{_xml_text(labels)}</data>")
        lines.append(f"      <data key=\"props\">{props}</data>")
        lines.append("    </node>")
    for rel in document["relationships"]:
        edge_id = _xml_id("e", rel["id"])
        source = _xml_id("n", rel["start"])
        target = _xml_id("n", rel["end"])
        props = _xml_text(json.dumps(rel["properties"], ensure_ascii=False))
        lines.append(
            f'    <edge id="{edge_id}" source="{source}" target="{target}">'
        )
        lines.append(f"      <data key=\"type\">{_xml_text(str(rel['type']))}</data>")
        lines.append(f"      <data key=\"eprops\">{props}</data>")
        lines.append("    </edge>")
    lines.append("  </graph>")
    lines.append("</graphml>")
    xml = "\n".join(lines) + "\n"
    ET.fromstring(xml)
    return xml


def _xml_text(value: str) -> str:
    return escape(_INVALID_XML.sub("", value))


def _xml_id(prefix: str, value: Any) -> str:
    raw = str(value)
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in raw)
    return escape(f"{prefix}-{safe}")
