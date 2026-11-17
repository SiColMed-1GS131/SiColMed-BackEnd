"""Reglas de negocio de solicitudes de cambio."""
from typing import Any

from sqlalchemy.orm import Session

from app.errors import UsuarioSinMedico
from app.repositories import solicitudes_cambio as repo
from app.repositories.auth import AuthRepository
from app.schemas.solicitudes_cambio import (
    SolicitudCambioCrear,
    SolicitudCambioProcesar,
)


def listar_solicitudes(db: Session, estado: str | None) -> list[dict[str, Any]]:
    """Devuelve la bandeja de solicitudes, filtrada por estado si se indica."""
    return repo.listar_solicitudes_cambio(db, estado)


def obtener_id_medico(db: Session, usuario: Any) -> int:
    """Resuelve el médico del usuario autenticado.

    Reutiliza `id_medico`, que ya viaja en el JWT cuando el usuario es médico.
    Si no viene, consulta la relación 1:1 con la función equivalente existente
    `AuthRepository.obtener_id_medico`.
    """
    id_medico = (
        usuario.get("id_medico")
        if isinstance(usuario, dict)
        else getattr(usuario, "id_medico", None)
    )
    if isinstance(id_medico, int) and id_medico >= 1:
        return id_medico

    id_usuario = (
        usuario.get("id_usuario")
        if isinstance(usuario, dict)
        else getattr(usuario, "id_usuario", None)
    )
    if not isinstance(id_usuario, int) or id_usuario < 1:
        raise UsuarioSinMedico()

    id_medico = AuthRepository(db).obtener_id_medico(id_usuario)
    if id_medico is None:
        raise UsuarioSinMedico()
    return id_medico


def armar_cambios(solicitud: SolicitudCambioCrear) -> dict[str, Any]:
    """Objeto JSONB por secciones que espera `crear_solicitud_cambio`."""
    return solicitud.model_dump(exclude_none=True)


def armar_decisiones(solicitud: SolicitudCambioProcesar) -> dict[str, Any]:
    """Objeto JSONB de decisiones que espera `procesar_solicitud_cambio`."""
    return solicitud.model_dump(exclude_none=True, exclude={"comentario"})


def crear_solicitud(
    db: Session,
    usuario: Any,
    solicitud: SolicitudCambioCrear,
) -> int:
    """Crea una solicitud para el médico asociado al usuario autenticado."""
    id_medico = obtener_id_medico(db, usuario)
    return repo.crear_solicitud_cambio(db, id_medico, armar_cambios(solicitud))


def procesar_solicitud_cambio(
    db: Session,
    id_solicitud_cambio: int,
    id_administrador: int,
    solicitud: SolicitudCambioProcesar,
) -> bool:
    """Procesa la solicitud con las decisiones del administrador."""
    return repo.procesar_solicitud_cambio(
        db,
        id_solicitud_cambio,
        id_administrador,
        armar_decisiones(solicitud),
        solicitud.comentario,
    )
