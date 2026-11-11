"""Rutas del repositorio y salidas que no deben versionarse."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Directorio del proyecto, tanto en un checkout como con cwd puesto ahí."""
    markers = ("pyproject.toml", "docker-compose.yml")
    here = Path(__file__).resolve()
    candidates = list(here.parents)
    cwd = Path.cwd()
    candidates.extend([cwd, *cwd.parents])
    for parent in candidates:
        if all((parent / name).exists() for name in markers):
            return parent
    return cwd


def dumps_dir() -> Path:
    path = repo_root() / "dumps"
    path.mkdir(parents=True, exist_ok=True)
    return path


def assert_ignored_output(path: Path) -> Path:
    """Solo se escribe dentro de dumps/ o data/, que están en .gitignore."""
    root = repo_root()
    resolved = path.resolve()
    allowed = [(root / "dumps").resolve(), (root / "data").resolve()]
    if any(resolved == base or base in resolved.parents for base in allowed):
        return resolved
    raise SystemExit(
        f"La salida tiene que quedar en dumps/ o data/ (están en .gitignore). "
        f"Ruta rechazada: {resolved}"
    )
