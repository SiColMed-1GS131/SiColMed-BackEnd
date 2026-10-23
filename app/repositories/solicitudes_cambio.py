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
    db: Session, id_medico: int, cambios: dict[str, dict[str, Any]]
) -> int:
    """Llama a crear_solicitud_cambio(id_medico, cambios).

    Devuelve el id de la solicitud creada (la función de BD retorna integer).  
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


def procesar_solicitud_cambio(
    db: Session,
    id_solicitud_cambio: int,
    id_administrador: int,
    decisiones: dict[str, dict[str, str]],
    comentario: str | None = None,
) -> bool:
    """Llama a procesar_solicitud_cambio con las decisiones del administrador."""
    return llamar_escalar(
        db,
        "procesar_solicitud_cambio",
        {
            "id_solicitud_cambio": Arg(id_solicitud_cambio, "integer"),
            "id_administrador": Arg(id_administrador, "integer"),
            "decisiones": Arg(decisiones, "jsonb"),
            "comentario": Arg(comentario, "text"),
        },
        commit=True,
    )
