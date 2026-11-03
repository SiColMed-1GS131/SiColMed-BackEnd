"""Pruebas de movimientos y reportes contables (Módulo 5). No necesitan una base de datos."""

from datetime import date

import pytest

from app.main import app
from app.repositories.movimientos import get_movimientos_repository
from app.repositories.reportes import get_reportes_repository
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado

MOVIMIENTO_VALIDO = {
    "fecha": "2026-11-02",
    "descripcion": "Cobro de cuotas",
    "detalle": [
        {"id_cuenta": 1, "monto": 100.5, "tipo": "DEBITO"},
        {"id_cuenta": 3, "monto": 100.5, "tipo": "CREDITO"},
    ],
}


class RepositorioMovimientosFalso:
    def __init__(self):
        self.llamadas = []

    def registrar(self, fecha, descripcion, detalle):
        self.llamadas.append(("registrar", fecha, descripcion, detalle))
        return 9

    def consultar_diarios(self, fecha):
        self.llamadas.append(("diarios", fecha))
        return [
            {"id_movimiento": 9, "fecha": fecha, "descripcion": "Cobro", "id_cuenta": 1,
             "nombre_cuenta": "Caja", "tipo": "DEBITO", "monto": 100.5},
        ]

    def consultar_por_cuenta(self, id_cuenta, fecha_inicio, fecha_fin):
        self.llamadas.append(("por_cuenta", id_cuenta, fecha_inicio, fecha_fin))
        return []


class RepositorioReportesFalso:
    def __init__(self):
        self.llamadas = []

    def balance_general(self, fecha_inicio, fecha_fin):
        self.llamadas.append(("balance", fecha_inicio, fecha_fin))
        return [
            {"id_cuenta": 1, "nombre_cuenta": "Caja", "total_debito": 10,
             "total_credito": 4, "saldo": 6},
        ]


def _como(rol):
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1, rol=rol
    )


@pytest.fixture
def repo_mov(cliente):
    falso = RepositorioMovimientosFalso()
    app.dependency_overrides[get_movimientos_repository] = lambda: falso
    _como(roles.TESORERO)
    return falso


@pytest.fixture
def repo_rep(cliente):
    falso = RepositorioReportesFalso()
    app.dependency_overrides[get_reportes_repository] = lambda: falso
    _como(roles.ADMIN_ASOCIACION)
    return falso


# --- Movimientos -------------------------------------------------------------

def test_registrar_envia_detalle_a_la_bd(cliente, repo_mov):
    respuesta = cliente.post("/movimientos", json=MOVIMIENTO_VALIDO)

    assert respuesta.status_code == 201
    assert respuesta.json()["id_movimiento"] == 9
    assert repo_mov.llamadas == [(
        "registrar",
        date(2026, 11, 2),
        "Cobro de cuotas",
        [
            {"id_cuenta": 1, "monto": 100.5, "tipo": "DEBITO"},
            {"id_cuenta": 3, "monto": 100.5, "tipo": "CREDITO"},
        ],
    )]


def test_registrar_rechaza_formato_plano(cliente, repo_mov):
    plano = {"fecha": "2026-11-02", "descripcion": "x", "id_cuenta": 1,
             "monto": "1.00", "tipo": "DEBITO"}

    assert cliente.post("/movimientos", json=plano).status_code == 422
    assert repo_mov.llamadas == []


def test_registrar_rechaza_movimiento_que_no_cuadra(cliente, repo_mov):
    descuadrado = {**MOVIMIENTO_VALIDO, "detalle": [
        {"id_cuenta": 1, "monto": 10, "tipo": "DEBITO"},
        {"id_cuenta": 3, "monto": 9, "tipo": "CREDITO"},
    ]}

    assert cliente.post("/movimientos", json=descuadrado).status_code == 422


def test_movimientos_diarios(cliente, repo_mov):
    respuesta = cliente.get("/movimientos", params={"fecha": "2026-11-02"})

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["nombre_cuenta"] == "Caja"
    assert repo_mov.llamadas == [("diarios", date(2026, 11, 2))]


def test_movimientos_por_cuenta_usa_fecha_inicio_y_fecha_fin(cliente, repo_mov):
    respuesta = cliente.get(
        "/cuentas/3/movimientos",
        params={"fecha_inicio": "2026-11-01", "fecha_fin": "2026-11-30"},
    )

    assert respuesta.status_code == 200
    assert repo_mov.llamadas == [("por_cuenta", 3, date(2026, 11, 1), date(2026, 11, 30))]


def test_movimientos_por_cuenta_sin_rango_devuelve_422(cliente, repo_mov):
    respuesta = cliente.get("/cuentas/3/movimientos", params={"inicio": "2026-11-01"})

    assert respuesta.status_code == 422


def test_movimientos_rechaza_rol_sin_permiso(cliente, repo_mov):
    _como(roles.MEDICO)

    assert cliente.get("/movimientos", params={"fecha": "2026-11-02"}).status_code == 403


def test_movimientos_sin_token_devuelve_401(cliente, repo_mov):
    app.dependency_overrides.pop(get_usuario_actual)

    assert cliente.get("/movimientos", params={"fecha": "2026-11-02"}).status_code == 401


# --- Reportes ----------------------------------------------------------------

def test_balance_general(cliente, repo_rep):
    respuesta = cliente.get(
        "/reportes/balance-general",
        params={"fecha_inicio": "2026-11-01", "fecha_fin": "2026-11-30"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["filas"][0]["saldo"] == 6
    assert repo_rep.llamadas == [("balance", date(2026, 11, 1), date(2026, 11, 30))]


def test_balance_rechaza_rol_sin_permiso(cliente, repo_rep):
    _como(roles.TESORERO)

    respuesta = cliente.get(
        "/reportes/balance-general",
        params={"fecha_inicio": "2026-11-01", "fecha_fin": "2026-11-30"},
    )

    assert respuesta.status_code == 403
