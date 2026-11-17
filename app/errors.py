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
    """El usuario autenticado no tiene un médico asociado."""


# DEF-018: el texto de PostgreSQL solo se muestra cuando viene de un RAISE EXCEPTION de
# nuestras funciones (SQLSTATE P0001), porque ya está escrito para el usuario. Los demás
# errores (restricciones, tipos, valores fuera de rango, bytes NUL...) traen detalles
# internos, así que responden con un mensaje propio. El código sigue siendo 400 en todos
# los casos (decisión 6 del líder).
_RAISE_EXCEPTION = "P0001"
_MENSAJES_POR_SQLSTATE = {
    "23505": "Ya existe un registro con esos datos.",
    "23503": "Uno de los datos relacionados no existe.",
    "23502": "Falta un dato obligatorio.",
    "23514": "Uno de los datos no cumple las reglas permitidas.",
    "22001": "Un texto supera la longitud permitida.",
    "22003": "Un valor numérico está fuera del rango permitido.",
}
MENSAJE_ERROR_BD = "No se pudo completar la operación con los datos enviados."


def _sqlstate(error: DBAPIError) -> str | None:
    original: Any = error.orig
    diagnostico: Any = getattr(original, "diag", None)
    return getattr(original, "sqlstate", None) or getattr(diagnostico, "sqlstate", None)


def _obtener_mensaje_bd(error: DBAPIError) -> str:
    """Mensaje para el usuario: el del RAISE EXCEPTION o uno propio, nunca el interno."""
    diagnostico: Any = getattr(error.orig, "diag", None)
    mensaje = getattr(diagnostico, "message_primary", None)
    estado = _sqlstate(error)

    # Sin SQLSTATE pero con mensaje principal: es la forma en que las pruebas simulan un
    # RAISE EXCEPTION. Un error real de PostgreSQL siempre trae su SQLSTATE.
    if mensaje and estado in (None, _RAISE_EXCEPTION):
        return str(mensaje)
    return _MENSAJES_POR_SQLSTATE.get(estado or "", MENSAJE_ERROR_BD)


async def manejar_error_bd(request: Request, error: DBAPIError) -> JSONResponse:
    """Convierte un error de PostgreSQL en una respuesta HTTP 400."""
    return JSONResponse(
        status_code=400,
        content={"detail": _obtener_mensaje_bd(error)},
    )
