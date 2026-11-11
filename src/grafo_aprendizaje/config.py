"""Conexión a Neo4j a partir de .env, sin valores por defecto secretos."""

from __future__ import annotations

import os
from dataclasses import dataclass

from grafo_aprendizaje.paths import repo_root


@dataclass(frozen=True)
class Settings:
    uri: str
    user: str
    password: str
    database: str


def load_settings() -> Settings:
    from dotenv import load_dotenv

    load_dotenv(repo_root() / ".env", override=False)
    uri = _first("UNGRAPH_NEO4J_URI", "NEO4J_URI") or "bolt://localhost:7687"
    user = _first("UNGRAPH_NEO4J_USER", "NEO4J_USER") or "neo4j"
    password = _first("UNGRAPH_NEO4J_PASSWORD", "NEO4J_PASSWORD")
    database = _first("UNGRAPH_NEO4J_DATABASE", "NEO4J_DATABASE") or "neo4j"
    if not password:
        raise SystemExit(
            "Falta la contraseña. Copia .env.example a .env y define "
            "NEO4J_PASSWORD (o UNGRAPH_NEO4J_PASSWORD)."
        )
    return Settings(uri=uri, user=user, password=password, database=database)


def configure_ungraph(settings: Settings) -> None:
    """Aplica la config pública de ungraph 0.1.5 (configure)."""
    import ungraph

    ungraph.configure(
        neo4j_uri=settings.uri,
        neo4j_user=settings.user,
        neo4j_password=settings.password,
        neo4j_database=settings.database,
    )


def _first(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""
