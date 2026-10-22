"""Reglas de negocio de catálogos profesionales."""

from typing import Any

from sqlalchemy.orm import Session

from app.repositories import catalogos_profesionales as repo


def listar_especialidades(db: Session) -> list[dict[str, Any]]:
    """Devuelve el catálogo de especialidades."""
    return repo.listar_especialidades(db)