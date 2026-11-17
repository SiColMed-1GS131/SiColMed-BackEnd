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
from app.security import roles
from app.security.auth import UsuarioAutenticado, requiere_rol
from app.services import solicitudes_cambio as service

router = APIRouter(prefix="/solicitudes-cambio", tags=["Solicitudes de cambio"])


@router.post(
    "",
    response_model=SolicitudCambioCreada,
    status_code=status.HTTP_201_CREATED,
    summary="Crear solicitud de cambio",
    description=(
        "El médico autenticado solicita cambios en su información laboral, "
        "estudios, certificaciones o relaciones profesionales."
    ),
    responses={
        400: {"description": "Error devuelto por la base de datos"},
        403: {"description": "El usuario autenticado no está asociado a un médico."},
    },
)
def crear_solicitud(
    solicitud: SolicitudCambioCrear,
    usuario: UsuarioAutenticado = Depends(requiere_rol(roles.MEDICO)),
    db: Session = Depends(get_db),
) -> SolicitudCambioCreada:
    try:
        id_solicitud_cambio = service.crear_solicitud(db, usuario, solicitud)
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
    _administrador: UsuarioAutenticado = Depends(requiere_rol(roles.ADMIN_CMP)),
    db: Session = Depends(get_db),
):
    return service.listar_solicitudes(db, estado)


@router.post(
    "/{id_solicitud_cambio}/procesar",
    response_model=bool,
    status_code=200,
    summary="Procesar solicitud de cambio",
    description="Aplica las decisiones del administrador sobre los cambios solicitados.",
    responses={
        400: {"description": "Error devuelto por la base de datos"},
        403: {"description": "El usuario autenticado no tiene el rol admin_cmp."},
    },
)
def procesar_solicitud(
    id_solicitud_cambio: int,
    solicitud: SolicitudCambioProcesar,
    administrador: UsuarioAutenticado = Depends(requiere_rol(roles.ADMIN_CMP)),
    db: Session = Depends(get_db),
) -> bool:
    return service.procesar_solicitud_cambio(
        db,
        id_solicitud_cambio,
        administrador.id_usuario,
        solicitud,
    )
