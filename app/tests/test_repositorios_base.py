"""Pruebas para app/repositories/base.py. No necesitan una base de datos."""

import json

import pytest

from app.repositories.base import (
    Arg,
    _construir_llamada,
    llamar_escalar,
    llamar_tabla,
)


class FakeResult:
    def scalar_one(self):
        return 42

    def mappings(self):
        return self

    def all(self):
        return [{"id": 1}, {"id": 2}]


class FakeDb:
    def __init__(self, error=None):
        self.error = error
        self.sql = None
        self.values = None
        self.commits = 0
        self.rollbacks = 0

    def execute(self, statement, values):
        if self.error:
            raise self.error
        self.sql = str(statement)
        self.values = values
        return FakeResult()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


# --- Construcción de la llamada ---------------------------------------------


def test_sin_parametros():
    sql, values = _construir_llamada("list_something", None)
    assert sql == "list_something()"
    assert values == {}


def test_los_parametros_simples_conservan_el_orden():
    sql, values = _construir_llamada("f", {"a": 1, "b": "x"})
    assert sql == "f(:a, :b)"
    assert values == {"a": 1, "b": "x"}


def test_cast_para_valores_nulos():
    sql, values = _construir_llamada(
        "filter_doctors",
        {"last_name": Arg(None, "text"), "province_id": Arg(3, "integer")},
    )
    assert sql == (
        "filter_doctors(CAST(:last_name AS text), CAST(:province_id AS integer))"
    )
    assert values == {"last_name": None, "province_id": 3}


def test_json_se_serializa():
    changes = {"field": {"old": "1", "new": "2"}}
    sql, values = _construir_llamada(
        "create_request",
        {"doctor_id": Arg(10, "integer"), "changes": Arg(changes, "jsonb")},
    )
    assert sql == (
        "create_request(CAST(:doctor_id AS integer), CAST(:changes AS jsonb))"
    )
    assert json.loads(values["changes"]) == changes


def test_json_none_se_mantiene_nulo():
    _, values = _construir_llamada("f", {"data": Arg(None, "jsonb")})
    assert values["data"] is None


def test_tipo_con_precision():
    sql, _ = _construir_llamada("register_entry", {"amount": Arg(10, "numeric(12,2)")})
    assert sql == "register_entry(CAST(:amount AS numeric(12,2)))"


# --- Validaciones de seguridad ----------------------------------------------


@pytest.mark.parametrize("name", ["Drop Table", "f; DROP TABLE doctor", "1abc", "a-b"])
def test_rechaza_nombres_de_funcion_peligrosos(name):
    with pytest.raises(ValueError):
        _construir_llamada(name, None)


def test_rechaza_nombre_de_parametro_peligroso():
    with pytest.raises(ValueError):
        _construir_llamada("f", {"a); DROP": 1})


def test_rechaza_tipo_peligroso():
    with pytest.raises(ValueError):
        _construir_llamada("f", {"a": Arg(1, "integer); DROP TABLE x; --")})


# --- Ejecución (con una base de datos simulada) -----------------------------


def test_escalar_sin_confirmar():
    db = FakeDb()
    assert llamar_escalar(db, "f", {"a": 1}) == 42
    assert db.sql == "SELECT f(:a)"
    assert db.values == {"a": 1}
    assert db.commits == 0


def test_escalar_con_confirmacion():
    db = FakeDb()
    llamar_escalar(db, "f", commit=True)
    assert db.commits == 1


def test_tabla_devuelve_lista_de_diccionarios():
    db = FakeDb()
    assert llamar_tabla(db, "g") == [{"id": 1}, {"id": 2}]
    assert db.sql == "SELECT * FROM g()"


def test_fallo_revierte_y_vuelve_a_lanzar():
    db = FakeDb(error=RuntimeError("failed"))
    with pytest.raises(RuntimeError):
        llamar_escalar(db, "f", commit=True)
    assert db.rollbacks == 1
    assert db.commits == 0