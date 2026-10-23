"""Endpoints de solicitudes de cambio."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.solicitudes_cambio import EstadoSolicitud, SolicitudCambioItem
from app.services import solicitudes_cambio as service
from app.schemas.solicitudes_cambio import SolicitudCambioProcesar
from app.security.auth import get_usuario_actual, requiere_rol



router = APIRouter(prefix="/solicitudes-cambio", tags=["Solicitudes de cambio"])


@router.get(
    "",
    response_model=list[SolicitudCambioItem],
    status_code=200,
    summary="Listar solicitudes de cambio",
    description="Bandeja del administrador. Sin filtro devuelve todas las solicitudes.",
    responses={400: {"description": "Error devuelto por la base de datos"}},
)
def listar_solicitudes(
    estado: EstadoSolicitud | None = Query(
        default=None,
        description="Filtra por estado general de la solicitud.",
        examples=["PENDIENTE"],
    ),
    db: Session = Depends(get_db),
):
    # PENDIENTE: aquí va la dependencia de permisos (requiere_rol), solo administrador.
    return service.listar_solicitudes(db, estado)

@router.post(
    "/{id_solicitud_cambio}/procesar",
    response_model=bool,
    status_code=200,
    summary="Procesar solicitud de cambio",
    description="Aplica las decisiones del administrador sobre los cambios solicitados.",
    responses={400: {"description": "Error devuelto por la base de datos"}},
)
def procesar_solicitud(
    id_solicitud_cambio: int,
    solicitud: SolicitudCambioProcesar,
    usuario_actual=Depends(get_usuario_actual),
    _=Depends(requiere_rol("admin_cmp")),
    db: Session = Depends(get_db),
) -> bool:
    """Procesa las decisiones del administrador sobre una solicitud."""
    id_administrador = (
        usuario_actual["id_usuario"]
        if isinstance(usuario_actual, dict)
        else usuario_actual.id_usuario
    )
    decisiones = {
        campo: decision.model_dump()
        for campo, decision in solicitud.decisiones.items()
    }
    return service.procesar_solicitud_cambio(
        db,
        id_solicitud_cambio,
        id_administrador,
        decisiones,
        solicitud.comentario,
    )
