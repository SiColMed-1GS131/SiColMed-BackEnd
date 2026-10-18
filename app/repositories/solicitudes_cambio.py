"""Acceso a datos de solicitudes de cambio."""
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.base import Arg, llamar_escalar, llamar_tabla


def listar_solicitudes_cambio(
    db: Session, estado: str | None
) -> list[dict[str, Any]]:
    """Llama a listar_solicitudes_cambio(estado). None trae todas."""
    return llamar_tabla(
        db,
        "listar_solicitudes_cambio",
        {"estado": Arg(estado, "text")},
    )


def crear_solicitud_cambio(
    db: Session, id_medico: int, cambios: dict[str, dict[str, str]]
) -> Any:
    """Llama a crear_solicitud_cambio(id_medico, cambios).

    PENDIENTE (BD): el doc dice que retorna "Integer o bool". Se devuelve
    tal cual, sin interpretar, hasta que BD confirme cuál es.
    """
    return llamar_escalar(
        db,
        "crear_solicitud_cambio",
        {
            "id_medico": Arg(id_medico, "integer"),
            "cambios": Arg(cambios, "jsonb"),
        },
        commit=True,
    )
