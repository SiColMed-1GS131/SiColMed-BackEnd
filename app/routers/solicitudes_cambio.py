"""Endpoints de solicitudes de cambio."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import UsuarioSinMedico
from app.schemas.solicitudes_cambio import (
    EstadoSolicitud,
    SolicitudCambioCreada,
    SolicitudCambioCrear,
    SolicitudCambioItem,
    SolicitudCambioProcesar,
)
from app.services import solicitudes_cambio as service
from app.security.auth import get_usuario_actual, requiere_rol


router = APIRouter(prefix="/solicitudes-cambio", tags=["Solicitudes de cambio"])


@router.post(
    "",
    response_model=SolicitudCambioCreada,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitud de cambio",
    description="El médico autenticado solicita cambios en su perfil.",
    responses={
        400: {"description": "Error devuelto por la base de datos"},
        403: {"description": "El usuario autenticado no está asociado a un médico."},
    },
)
def crear_solicitud(
    solicitud: SolicitudCambioCrear,
    usuario=Depends(requiere_rol("medico")),
    db: Session = Depends(get_db),
) -> SolicitudCambioCreada:
    try:
        id_solicitud_cambio = service.crear_solicitud(
            db, usuario, solicitud.cambios
        )
    except UsuarioSinMedico as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario autenticado no está asociado a un médico.",
        ) from error
    return SolicitudCambioCreada(id_solicitud_cambio=id_solicitud_cambio)


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
