# Grafo de aprendizaje

Esqueleto del grafo léxico personal de Miguel Giraldo Duque. Un documento local entra con [ungraph](https://pypi.org/project/ungraph/) 0.1.5 (Alejandro Giraldo Londoño / QNOW) y queda en Neo4j 5 como `File → Page → Chunk`, con embeddings. Un servidor [FastMCP](https://gofastmcp.com) 4.1.8 deja que Grok Bot, u otro agente, consulte ese grafo por stdio. Este repositorio es solo el código.

```
File -[:CONTAINS]-> Page -[:HAS_CHUNK]-> Chunk
Chunk -[:NEXT_CHUNK]-> Chunk
```

El archivo y la página no van en el nodo `Chunk`. ungraph los guarda en `File.filename` y `Page.page_number`.

## Requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker con Compose

## Neo4j

```bash
cp .env.example .env
# Cambia NEO4J_PASSWORD (mínimo 8 caracteres) en los dos bloques del archivo.
docker compose up -d
```

El navegador queda en <http://localhost:7474> (usuario `neo4j`, contraseña la de `.env`). Bolt es `bolt://localhost:7687`. La imagen es `neo4j:5.26.31`. Los datos viven en `data/neo4j/` y las copias en `dumps/`.

## Instalar

```bash
uv sync
```

La primera ingesta o búsqueda descarga `sentence-transformers/all-MiniLM-L6-v2`. ungraph 0.1.5 crea el índice vectorial con 384 dimensiones para ese modelo; no lo cambies.

## Ingerir

El archivo se queda fuera del repo. ungraph 0.1.5 acepta Markdown (`.md`, `.markdown`), TXT, Word (`.doc`, `.docx`) y PDF.

```bash
uv run grafo-ingerir /ruta/local/notas.md
```

Eso llama a `ungraph.configure(...)` y a `ungraph.ingest_document(ruta)`, que arma el grafo `File → Page → Chunk` con embeddings. Al terminar imprime título, archivo, páginas y cantidad de chunks.

Opciones: `--chunk-size` (1000) y `--chunk-overlap` (200), los valores por defecto de ungraph.

En esta versión de ungraph, `ingest_document` procesa el primer documento que devuelve el cargador. En Markdown y TXT la página suele quedar en `1` porque el loader no trae `page_number`. En un PDF, el número de página es el que Docling ponga en los metadatos de ese primer documento.

## Servidor MCP

```bash
uv run grafo-mcp
```

Equivalente: `uv run python -m grafo_aprendizaje.mcp_server`.

El proceso habla FastMCP por stdin/stdout (`mcp.run(transport="stdio")`). No imprime el protocolo por la terminal: lo lanza el cliente. La contraseña la lee de `.env` (`NEO4J_*` o `UNGRAPH_*`). El directorio de trabajo del conector tiene que ser este repo, para encontrar `.env`.

Ejemplo de conector stdio:

```json
{
  "command": "uv",
  "args": ["run", "grafo-mcp"],
  "cwd": "/ruta/absoluta/grafo-aprendizaje"
}
```

También vale `uv run python -m grafo_aprendizaje.mcp_server` en `args`.

Herramientas:

| Herramienta | Qué hace |
| --- | --- |
| `search` | `hybrid` (por defecto, `ungraph.hybrid_search`), `vector` (`ungraph.vector_search`) o `text` (`ungraph.search`). Devuelve extractos cortos con archivo, página, `chunk_id` y puntaje. |
| `get_passage` | Texto guardado de un archivo y una página, en orden `chunk_id_consecutive`. El solapamiento de chunks puede repetir frases. |
| `related` | Vecinos de un `chunk_id`. Si ese id no existe, `ref` se trata como idea y se resuelve con `hybrid_search` y, si no hay intersección, con `vector_search`. |

`hybrid_search` de ungraph 0.1.5 solo devuelve chunks que salen a la vez en el índice de texto y en el vectorial. Si una consulta híbrida vuelve vacía, repite con `mode="vector"`.

## Copia y restauración

Los dos scripts usan la misma imagen del compose, con la base detenida (Community no vuelca una base montada). Paran Neo4j, corren `neo4j-admin` y lo vuelven a arrancar.

```bash
./scripts/neo4j-dump.sh
./scripts/neo4j-load.sh
```

El volcado es `dumps/neo4j.dump` (o `dumps/<NEO4J_DATABASE>.dump`). `load` sustituye la base local con ese archivo. `neo4j-admin` corre como el usuario `neo4j` (uid 7474); el script deja `dumps/` escribible para ese usuario.

Para mirar nodos y relaciones sin restaurar la base:

```bash
uv run grafo-exportar
```

Escribe `dumps/grafo.json` y `dumps/grafo.graphml`. Los vectores se omiten. `--include-embeddings` los deja en el archivo, que pasa a ser grande. La salida solo se acepta dentro de `dumps/` o `data/`.

## Qué no entra en git

PDFs, libros, texto de obras, exports, volcados, datos de Neo4j, cachés de embeddings y `.env`. El código y `.env.example` (contraseña de ejemplo, no un secreto real) sí.

Antes de un commit, si algo de estudio está en el árbol, no lo agregues. Las carpetas `data/`, `dumps/`, `volumes/`, `libros/`, `documentos/` y `corpus/`, más `*.pdf` y `*.dump`, están en `.gitignore`.
