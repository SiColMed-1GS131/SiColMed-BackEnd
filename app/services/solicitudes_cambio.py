"""Reglas de negocio de solicitudes de cambio."""
from typing import Any

from sqlalchemy.orm import Session

from app.repositories import solicitudes_cambio as repo
from app.schemas.solicitudes_cambio import CambioRelacionSolicitado, CambioSolicitado


def listar_solicitudes(db: Session, estado: str | None) -> list[dict[str, Any]]:
    """Devuelve la bandeja de solicitudes, filtrada por estado si se indica."""
    return repo.listar_solicitudes_cambio(db, estado)


def armar_cambios(
    cambios: list[CambioSolicitado | CambioRelacionSolicitado],
) -> dict[str, dict[str, Any]]:
    """Convierte los cambios al objeto JSONB que espera la función de BD."""
    normalizados: dict[str, dict[str, Any]] = {}
    for cambio in cambios:
        if isinstance(cambio, CambioRelacionSolicitado):
            normalizados[cambio.campo] = {
                "agregar": cambio.agregar,
                "quitar": cambio.quitar,
            }
        else:
            normalizados[cambio.campo] = {"valor_nuevo": cambio.valor_nuevo}
    return normalizados


def crear_solicitud(
    db: Session, id_medico: int, cambios: list[CambioSolicitado | CambioRelacionSolicitado]
) -> int:
    """Crea una solicitud de cambio para el médico indicado.

    Transforma la lista validada en el diccionario por campo y delega en el
    repository. El retorno se pasa tal cual (pendiente de confirmar con BD).
    """
    return repo.crear_solicitud_cambio(db, id_medico, armar_cambios(cambios))


def procesar_solicitud_cambio(
    db: Session,
    id_solicitud_cambio: int,
    id_administrador: int,
    decisiones: dict[str, dict[str, str]],
    comentario: str | None = None,
) -> bool:
    """Procesa la solicitud de cambio con las decisiones del administrador."""
    return repo.procesar_solicitud_cambio(
        db,
        id_solicitud_cambio,
        id_administrador,
        decisiones,
        comentario,
    )
