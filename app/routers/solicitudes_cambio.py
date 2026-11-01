"""Endpoints de solicitudes de cambio."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.solicitudes_cambio import EstadoSolicitud, SolicitudCambioItem
from app.security import roles
from app.security.auth import UsuarioAutenticado, requiere_rol
from app.services import solicitudes_cambio as service

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
    _administrador: UsuarioAutenticado = Depends(
        requiere_rol(roles.ADMIN_CMP)
    ),
    db: Session = Depends(get_db),
):
    return service.listar_solicitudes(db, estado)