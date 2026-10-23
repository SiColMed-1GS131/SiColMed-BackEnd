"""Reglas de negocio de catálogos profesionales."""

from typing import Any

from sqlalchemy.orm import Session

from app.repositories import catalogos_profesionales as repo


def listar_especialidades(db: Session) -> list[dict[str, Any]]:
    """Devuelve el catálogo de especialidades."""
    return repo.listar_especialidades(db)


def listar_subespecialidades(
    db: Session, id_especialidad: int | None = None
) -> list[dict[str, Any]]:
    """Devuelve el catálogo de subespecialidades."""
    return repo.listar_subespecialidades(db, id_especialidad)


def listar_asociaciones(db: Session) -> list[dict[str, Any]]:
    """Devuelve el catálogo de asociaciones."""
    return repo.listar_asociaciones(db)
