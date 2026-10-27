from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.medicos import ContratoBDPendiente
from app.schemas.medicos import MedicoCreado, MedicoRegistro, PerfilMedico
from app.services import medicos as service

router = APIRouter(prefix="/medicos", tags=["Médicos"])

def requiere_administrador() -> Any:
    """Punto de integración temporal; reemplazar por requiere_rol de Login.

    Nunca autorizar registros sin comprobar permisos.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Pendiente integración de permiso de administrador con Login",
    )

@router.post("", response_model=MedicoCreado, status_code=status.HTTP_201_CREATED,
             summary="Registrar un médico (administrador)")
def crear_medico(
    datos: MedicoRegistro,
    _administrador: Any = Depends(requiere_administrador),
    db: Session = Depends(get_db),
):
    try:
        return {"id_medico": service.registrar_medico(db, datos)}
    except ContratoBDPendiente as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@router.get("/{id_medico}", response_model=PerfilMedico,
            summary="Obtener perfil de médico por ID")
def consultar_medico(
    id_medico: int = Path(gt=0, description="ID único del médico"),
    db: Session = Depends(get_db),
):
    resultado = service.obtener_perfil_medico(db, id_medico)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    if not isinstance(resultado, dict):
        raise HTTPException(status_code=502, detail="Formato de perfil no válido desde BD")
    return resultado
