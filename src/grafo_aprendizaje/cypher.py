"""Consultas sobre el patrón File-Page-Chunk que escribe ungraph 0.1.5.

El nodo Chunk no guarda filename ni page_number. Esos datos viven en
File y Page, unidos por CONTAINS y HAS_CHUNK
(ver ungraph.utils.graph_operations.extract_document_structure).
"""

SOURCES_BY_CHUNK = """
UNWIND $ids AS chunk_id
MATCH (f:File)-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk {chunk_id: chunk_id})
RETURN chunk_id AS chunk_id, f.filename AS source, p.page_number AS page
"""

CHUNK_EXISTS = """
MATCH (c:Chunk {chunk_id: $chunk_id})
RETURN c.chunk_id AS chunk_id
LIMIT 1
"""

PAGE_CHUNKS = """
MATCH (f:File)-[:CONTAINS]->(p:Page)-[:HAS_CHUNK]->(c:Chunk)
WHERE f.filename = $source AND p.page_number = $page
RETURN c.chunk_id AS chunk_id,
       c.chunk_id_consecutive AS n,
       c.page_content AS content
ORDER BY n ASC
"""

NEIGHBORS = """
MATCH (c:Chunk {chunk_id: $chunk_id})
CALL {
  WITH c
  OPTIONAL MATCH (p:Page)-[:HAS_CHUNK]->(c)
  OPTIONAL MATCH (f:File)-[:CONTAINS]->(p)
  RETURN f.filename AS source, p.page_number AS page
  LIMIT 1
}
CALL {
  WITH c
  // Vecinos directos: HAS_CHUNK (la Page), NEXT_CHUNK y cualquier otra relación.
  OPTIONAL MATCH (c)-[r]-(other)
  WITH c, r, other
  ORDER BY type(r), other.chunk_id_consecutive
  WITH c, collect(
    CASE WHEN r IS NULL THEN NULL ELSE {
      type: type(r),
      outgoing: startNode(r) = c,
      labels: labels(other),
      chunk_id: other.chunk_id,
      filename: other.filename,
      page_number: other.page_number,
      snippet: CASE
        WHEN other.page_content IS NULL THEN NULL
        ELSE substring(toString(other.page_content), 0, $snippet)
      END
    } END
  ) AS raw
  RETURN [x IN raw WHERE x IS NOT NULL][0..$limit] AS neighbors
}
RETURN c.chunk_id AS chunk_id,
       substring(c.page_content, 0, $passage) AS content,
       source AS source,
       page AS page,
       neighbors AS neighbors
"""

EXPORT_NODES = """
MATCH (n)
RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props
ORDER BY id
"""

EXPORT_RELATIONSHIPS = """
MATCH (a)-[r]->(b)
RETURN elementId(r) AS id,
       type(r) AS type,
       elementId(a) AS start,
       elementId(b) AS end,
       properties(r) AS props
ORDER BY id
"""
