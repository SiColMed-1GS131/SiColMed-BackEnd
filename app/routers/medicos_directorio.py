"""Rutas para filtros y actualización administrativa de médicos."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import MedicoNoEncontrado, RespuestaBDInvalida
from app.repositories.medicos_directorio import RepositorioMedicosDirectorio
from app.schemas.medicos_directorio import (
    ActualizarMedicoRespuesta,
    ActualizarMedicoSolicitud,
    ActualizarPerfilMedicoSolicitud,
    FiltroMedicos,
    ListaMedicosRespuesta,
)
from app.security.auth import requiere_rol
from app.services.medicos_directorio import (
    actualizar_medico,
    actualizar_perfil_medico,
    obtener_medicos,
)

router = APIRouter(prefix="/medicos", tags=["Médicos"])
repositorio = RepositorioMedicosDirectorio()


def _obtener_id_usuario(usuario: Any) -> int:
    """Obtiene el identificador del usuario autenticado."""
    valor = (
        usuario.get("id_usuario")
        if isinstance(usuario, dict)
        else getattr(usuario, "id_usuario", None)
    )
    if not isinstance(valor, int) or valor < 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La autenticación no entregó un id_usuario válido.",
        )
    return valor


def _obtener_id_medico(usuario: Any) -> int:
    """Obtiene el médico propietario del perfil autenticado."""
    valor = (
        usuario.get("id_medico")
        if isinstance(usuario, dict)
        else getattr(usuario, "id_medico", None)
    )
    if not isinstance(valor, int) or valor < 1:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La autenticación no entregó un id_medico válido.",
        )
    return valor


@router.get(
    "",
    response_model=ListaMedicosRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Listar y filtrar médicos",
)
def listar_medicos(
    filtros: FiltroMedicos = Depends(),
    db: Session = Depends(get_db),
) -> ListaMedicosRespuesta:
    try:
        return obtener_medicos(db, filtros, repositorio)
    except RespuestaBDInvalida as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error


@router.patch(
    "/{id_medico}/perfil",
    response_model=ActualizarMedicoRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Actualizar información no sensible del perfil",
)
def editar_perfil_medico(
    datos: ActualizarPerfilMedicoSolicitud,
    id_medico: int = Path(..., ge=1),
    usuario: Any = Depends(requiere_rol("medico")),
    db: Session = Depends(get_db),
) -> ActualizarMedicoRespuesta:
    try:
        if _obtener_id_medico(usuario) != id_medico:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puede actualizar su propio perfil.",
            )
        return actualizar_perfil_medico(
            db,
            id_medico,
            _obtener_id_usuario(usuario),
            datos,
            repositorio,
        )
    except MedicoNoEncontrado as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error


@router.patch(
    "/{id_medico}",
    response_model=ActualizarMedicoRespuesta,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos de un médico",
)
def editar_medico(
    datos: ActualizarMedicoSolicitud,
    id_medico: int = Path(..., ge=1),
    usuario: Any = Depends(requiere_rol("admin_cmp")),
    db: Session = Depends(get_db),
) -> ActualizarMedicoRespuesta:
    try:
        return actualizar_medico(
            db,
            id_medico,
            _obtener_id_usuario(usuario),
            datos,
            repositorio,
        )
    except MedicoNoEncontrado as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
