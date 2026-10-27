"""Rutas /auth/login, /auth/register y /auth/me."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DBAPIError
from app.schemas.auth import LoginSolicitud, RegistroSolicitud, TokenRespuesta, UsuarioRespuesta
from app.security.auth import UsuarioAutenticado, get_usuario_actual
from app.services.auth import AuthService, get_auth_service, CredencialesInvalidas, UsuarioInactivo, UsuarioNoEncontrado

router = APIRouter(prefix="/auth", tags=["Autenticación"])
Servicio = Annotated[AuthService, Depends(get_auth_service)]

def _inactivo():
    raise HTTPException(status_code=403, detail="La cuenta está inactiva.")

@router.post("/register", response_model=TokenRespuesta, status_code=status.HTTP_201_CREATED)
def registrar(datos: RegistroSolicitud, servicio: Servicio):
    try:
        return servicio.registrar(datos)
    except UsuarioNoEncontrado:
        raise HTTPException(status_code=404, detail="No se encontró la cuenta creada.") from None
    # Los errores SQL existentes se manejan mediante el manejador global DBAPIError.

@router.post("/login", response_model=TokenRespuesta)
def login(datos: LoginSolicitud, servicio: Servicio):
    try:
        return servicio.login(datos)
    except CredencialesInvalidas:
        raise HTTPException(status_code=401, detail="Credenciales inválidas.", headers={"WWW-Authenticate":"Bearer"}) from None
    except UsuarioInactivo:
        _inactivo()

@router.get("/me", response_model=UsuarioRespuesta)
def me(usuario: Annotated[UsuarioAutenticado, Depends(get_usuario_actual)], servicio: Servicio):
    try:
        return servicio.obtener_usuario(usuario.id_usuario)
    except UsuarioNoEncontrado:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.", headers={"WWW-Authenticate":"Bearer"}) from None
    except UsuarioInactivo:
        _inactivo()
