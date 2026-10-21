"""Acceso a datos de solicitudes de cambio."""
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.base import Arg, llamar_tabla


def listar_solicitudes_cambio(
    db: Session, estado: str | None
) -> list[dict[str, Any]]:
    """Llama a listar_solicitudes_cambio(estado). None trae todas."""
    return llamar_tabla(
        db,
        "listar_solicitudes_cambio",
        {"estado": Arg(estado, "text")},
    )

