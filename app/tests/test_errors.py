import asyncio
import json
from types import SimpleNamespace

import pytest
from fastapi import Request
from sqlalchemy.exc import DBAPIError

from app.errors import MENSAJE_ERROR_BD, manejar_error_bd


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


def test_error_bd_sin_diagnostico_no_muestra_el_mensaje_interno():
    # DEF-018: sin diagnóstico (por ejemplo, el error de psycopg por un byte NUL) el
    # texto original es interno; se responde un mensaje propio, siempre con 400.
    error = crear_error_bd(RuntimeError("PostgreSQL text fields cannot contain NUL (0x00) bytes"))

    respuesta = asyncio.run(manejar_error_bd(crear_solicitud_falsa(), error))

    assert respuesta.status_code == 400
    assert json.loads(respuesta.body) == {"detail": MENSAJE_ERROR_BD}


class ErrorPostgres(Exception):
    """Como las excepciones de psycopg: traen sqlstate y diag."""

    def __init__(self, sqlstate, mensaje):
        super().__init__(mensaje)
        self.sqlstate = sqlstate
        self.diag = SimpleNamespace(message_primary=mensaje, sqlstate=sqlstate)


def responder(sqlstate, mensaje):
    error = crear_error_bd(ErrorPostgres(sqlstate, mensaje))
    respuesta = asyncio.run(manejar_error_bd(crear_solicitud_falsa(), error))
    return respuesta.status_code, json.loads(respuesta.body)["detail"]


def test_raise_exception_real_muestra_su_mensaje():
    assert responder("P0001", "La cuenta 99 no existe") == (400, "La cuenta 99 no existe")


@pytest.mark.parametrize(
    "sqlstate, interno, esperado",
    [
        ("23505", 'duplicate key value violates unique constraint "cuenta_nombre_key"',
         "Ya existe un registro con esos datos."),
        ("22003", "numeric field overflow", "Un valor numérico está fuera del rango permitido."),
        ("23503", 'insert or update on table "medico" violates foreign key constraint',
         "Uno de los datos relacionados no existe."),
        ("22P02", 'invalid input syntax for type integer: "abc"', MENSAJE_ERROR_BD),
    ],
)
def test_errores_internos_de_postgresql_no_se_muestran(sqlstate, interno, esperado):
    codigo, detalle = responder(sqlstate, interno)

    assert codigo == 400  # decisión 6: siempre 400
    assert detalle == esperado
    assert interno not in detalle
