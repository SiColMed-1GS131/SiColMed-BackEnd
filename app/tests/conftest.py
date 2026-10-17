"""Fixtures comunes para las pruebas unitarias de la API.

Las pruebas no usan PostgreSQL: cada prueba reemplaza su repositorio por una
versión falsa con app.dependency_overrides.
"""

import os

# app.config exige DATABASE_URL al importarse. SQLAlchemy no se conecta hasta
# que alguien usa el motor, y el fixture `cliente` bloquea get_db, así que
# esta dirección nunca se contacta.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://pruebas:pruebas@localhost:5432/pruebas"
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402


def _bd_no_disponible():
    raise RuntimeError(
        "Las pruebas unitarias no usan PostgreSQL: reemplaza el repositorio "
        "con app.dependency_overrides."
    )


@pytest.fixture
def cliente():
    """Cliente HTTP de la API con la BD bloqueada; limpia los reemplazos al terminar."""
    app.dependency_overrides[get_db] = _bd_no_disponible
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
