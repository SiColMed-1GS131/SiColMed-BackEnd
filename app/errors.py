"""Manejadores de errores de la aplicación."""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError


class RespuestaBDInvalida(Exception):
    """La base de datos devolvió una estructura inesperada."""


class MedicoNoEncontrado(Exception):
    """El médico solicitado no existe o no puede ser actualizado."""


class UsuarioSinMedico(Exception):
    """El usuario autenticado no está asociado a un médico."""


def _obtener_mensaje_bd(error: DBAPIError) -> str:
    """Obtiene el mensaje principal enviado por PostgreSQL."""
    diagnostico: Any = getattr(error.orig, "diag", None)
    mensaje = getattr(diagnostico, "message_primary", None)
    if mensaje:
        return str(mensaje)

    if error.orig.args:
        return str(error.orig.args[0])

    return str(error)


async def manejar_error_bd(request: Request, error: DBAPIError) -> JSONResponse:
    """Convierte un RAISE EXCEPTION de PostgreSQL en una respuesta HTTP."""
    return JSONResponse(
        status_code=400,
        content={"detail": _obtener_mensaje_bd(error)},
    )
