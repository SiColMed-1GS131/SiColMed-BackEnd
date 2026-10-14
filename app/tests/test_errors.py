import asyncio
import json
from types import SimpleNamespace

from fastapi import Request
from sqlalchemy.exc import DBAPIError

from app.errors import manejar_error_bd


def crear_error_bd(original: Exception) -> DBAPIError:
    return DBAPIError("SELECT registrar_medico()", {}, original, False)


def crear_solicitud_falsa() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
            "root_path": "",
        }
    )


def test_maneja_raise_exception_con_el_mensaje_de_postgresql():
    error = crear_error_bd(
        RuntimeError(
            "error interno",
        )
    )
    error.orig.diag = SimpleNamespace(message_primary="El médico ya existe")

    respuesta = asyncio.run(manejar_error_bd(crear_solicitud_falsa(), error))

    assert respuesta.status_code == 400
    assert json.loads(respuesta.body) == {"detail": "El médico ya existe"}


def test_maneja_error_bd_sin_diagnostico_con_el_mensaje_original():
    error = crear_error_bd(RuntimeError("No se pudo guardar el registro"))

    respuesta = asyncio.run(manejar_error_bd(crear_solicitud_falsa(), error))

    assert respuesta.status_code == 400
    assert json.loads(respuesta.body) == {
        "detail": "No se pudo guardar el registro"
    }
