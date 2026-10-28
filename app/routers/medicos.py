from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.medicos import ContratoBDPendiente
from app.schemas.medicos import MedicoCreado, MedicoRegistro, PerfilMedico
from app.security import roles
from app.security.auth import UsuarioAutenticado, requiere_rol
from app.services import medicos as service

router = APIRouter(prefix="/medicos", tags=["Médicos"])

@router.post("", response_model=MedicoCreado, status_code=status.HTTP_201_CREATED,
             summary="Registrar un médico (administrador)")
def crear_medico(
    datos: MedicoRegistro,
    _administrador: UsuarioAutenticado = Depends(
        requiere_rol(roles.ADMIN_CMP)
    ),
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
    usuario: UsuarioAutenticado = Depends(
        requiere_rol(roles.MEDICO, roles.ADMIN_CMP)
    ),
    db: Session = Depends(get_db),
):
    if usuario.rol == roles.MEDICO and usuario.id_medico != id_medico:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puede consultar su propio perfil.",
        )
    resultado = service.obtener_perfil_medico(db, id_medico)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    if not isinstance(resultado, dict):
        raise HTTPException(status_code=502, detail="Formato de perfil no válido desde BD")
    return resultado
