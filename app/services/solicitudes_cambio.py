"""Reglas de negocio de solicitudes de cambio."""
from typing import Any

from sqlalchemy.orm import Session

from app.repositories import solicitudes_cambio as repo
from app.schemas.solicitudes_cambio import CambioSolicitado


def listar_solicitudes(db: Session, estado: str | None) -> list[dict[str, Any]]:
    """Devuelve la bandeja de solicitudes, filtrada por estado si se indica."""
    return repo.listar_solicitudes_cambio(db, estado)


def armar_cambios(cambios: list[CambioSolicitado]) -> dict[str, dict[str, str]]:
    """Convierte la lista de cambios en el diccionario por campo que espera BD.

    SUPUESTO (sin confirmar con BD): la función de BD completa valor_anterior
    y el estado PENDIENTE inicial, así que aquí solo se envía valor_nuevo.
    Los campos repetidos ya los rechaza el schema SolicitudCambioCrear.
    """
    return {c.campo: {"valor_nuevo": c.valor_nuevo} for c in cambios}
