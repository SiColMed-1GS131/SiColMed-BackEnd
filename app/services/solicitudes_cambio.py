"""Reglas de negocio de solicitudes de cambio."""
from typing import Any

from sqlalchemy.orm import Session

from app.repositories import solicitudes_cambio as repo


def listar_solicitudes(db: Session, estado: str | None) -> list[dict[str, Any]]:
    """Devuelve la bandeja de solicitudes, filtrada por estado si se indica."""
    return repo.listar_solicitudes_cambio(db, estado)

