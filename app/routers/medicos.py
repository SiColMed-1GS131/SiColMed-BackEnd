from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.medicos import ContratoBDPendiente
from app.schemas.medicos import (
    CertificadoSubido,
    FotoSubida,
    MedicoCreado,
    MedicoPublico,
    MedicoRegistro,
    PerfilMedico,
)
from app.security import roles
from app.security.auth import UsuarioAutenticado, get_usuario_opcional, requiere_rol
from app.services import certificados, fotos
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

@router.get(
    "/{id_medico}",
    response_model=MedicoPublico | PerfilMedico,
    summary="Obtener perfil de médico por ID",
    description=(
        "Público. Sin sesión devuelve la ficha del directorio (MedicoPublico). "
        "El administrador, o el médico consultando su propio perfil, recibe el "
        "perfil completo (PerfilMedico)."
    ),
)
def consultar_medico(
    id_medico: int = Path(gt=0, description="ID único del médico"),
    usuario: UsuarioAutenticado | None = Depends(get_usuario_opcional),
    db: Session = Depends(get_db),
):
    resultado = service.obtener_perfil_medico(db, id_medico)
    if resultado is None:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    if not isinstance(resultado, dict):
        raise HTTPException(status_code=502, detail="Formato de perfil no válido desde BD")

    ve_perfil_completo = usuario is not None and (
        usuario.rol == roles.ADMIN_CMP
        or (usuario.rol == roles.MEDICO and usuario.id_medico == id_medico)
    )
    if ve_perfil_completo:
        return PerfilMedico(resultado)
    return service.perfil_publico(resultado)


# --- Certificado de idoneidad (PDF) -------------------------------------------

def _exigir_admin_o_propio(usuario: UsuarioAutenticado, id_medico: int) -> None:
    if usuario.rol == roles.MEDICO and usuario.id_medico != id_medico:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puede gestionar el certificado de su propio perfil.",
        )


@router.post(
    "/{id_medico}/certificado",
    response_model=CertificadoSubido,
    status_code=status.HTTP_201_CREATED,
    summary="Subir el certificado de idoneidad (PDF, máx. 5 MB)",
    description="Solo el administrador o el propio médico. Reemplaza el PDF anterior.",
)
async def subir_certificado(
    archivo: UploadFile = File(description="PDF del certificado de idoneidad"),
    id_medico: int = Path(gt=0, description="ID único del médico"),
    usuario: UsuarioAutenticado = Depends(requiere_rol(roles.MEDICO, roles.ADMIN_CMP)),
    db: Session = Depends(get_db),
):
    _exigir_admin_o_propio(usuario, id_medico)
    try:
        ruta = await certificados.guardar_certificado(db, id_medico, archivo)
    except certificados.MedicoSinRegistro as error:
        raise HTTPException(status_code=404, detail="Médico no encontrado") from error
    except certificados.CertificadoDemasiadoGrande as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except certificados.CertificadoInvalido as error:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(error)) from error
    return CertificadoSubido(certificado_pdf=ruta, url=f"/medicos/{id_medico}/certificado")


@router.get(
    "/{id_medico}/certificado",
    response_class=FileResponse,
    summary="Descargar el certificado de idoneidad (PDF)",
    description="Solo el administrador o el propio médico.",
)
def descargar_certificado(
    id_medico: int = Path(gt=0, description="ID único del médico"),
    usuario: UsuarioAutenticado = Depends(requiere_rol(roles.MEDICO, roles.ADMIN_CMP)),
    db: Session = Depends(get_db),
):
    _exigir_admin_o_propio(usuario, id_medico)
    ruta = certificados.ruta_certificado(db, id_medico)
    if ruta is None:
        raise HTTPException(status_code=404, detail="El médico no tiene certificado registrado")
    return FileResponse(
        ruta,
        media_type="application/pdf",
        filename=f"certificado_idoneidad_{id_medico}.pdf",
    )


# --- Foto de perfil (JPG/PNG) ---------------------------------------------------

@router.post(
    "/{id_medico}/foto",
    response_model=FotoSubida,
    status_code=status.HTTP_201_CREATED,
    summary="Subir la foto de perfil (JPG o PNG, máx. 2 MB)",
    description="Solo el administrador o el propio médico. Reemplaza la foto anterior.",
)
async def subir_foto(
    archivo: UploadFile = File(description="Foto JPG o PNG"),
    id_medico: int = Path(gt=0, description="ID único del médico"),
    usuario: UsuarioAutenticado = Depends(requiere_rol(roles.MEDICO, roles.ADMIN_CMP)),
    db: Session = Depends(get_db),
):
    if usuario.rol == roles.MEDICO and usuario.id_medico != id_medico:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puede cambiar la foto de su propio perfil.",
        )
    try:
        ruta = await fotos.guardar_foto(db, id_medico, archivo)
    except fotos.MedicoSinRegistro as error:
        raise HTTPException(status_code=404, detail="Médico no encontrado") from error
    except fotos.FotoDemasiadoGrande as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except fotos.FotoInvalida as error:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(error)) from error
    return FotoSubida(foto=ruta, url=f"/medicos/{id_medico}/foto")


@router.get(
    "/{id_medico}/foto",
    response_class=FileResponse,
    summary="Foto de perfil del médico",
    description="Pública, como la ficha del directorio.",
)
def ver_foto(
    id_medico: int = Path(gt=0, description="ID único del médico"),
    db: Session = Depends(get_db),
):
    ruta = fotos.ruta_foto(db, id_medico)
    if ruta is None:
        raise HTTPException(status_code=404, detail="El médico no tiene foto registrada")
    return FileResponse(ruta, media_type=fotos.MEDIA_TYPES.get(ruta.suffix, "application/octet-stream"))
