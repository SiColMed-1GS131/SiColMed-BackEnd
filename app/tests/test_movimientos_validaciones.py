"""DEF-007 y DEF-019: validaciones de POST /movimientos.

Criterio: fecha obligatoria (422 si falta o es null), descripción no vacía, montos
Decimal con 2 decimales como máximo y del tamaño de numeric(12,2), y sin fechas futuras.
"""

from datetime import timedelta

import pytest

from app.main import app
from app.repositories.movimientos import get_movimientos_repository
from app.schemas.movimientos import hoy_en_panama
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado


class RepositorioMovimientosFalso:
    def __init__(self):
        self.llamadas = []

    def registrar(self, fecha, descripcion, detalle):
        self.llamadas.append((fecha, descripcion, detalle))
        return 9


@pytest.fixture
def repo(cliente):
    falso = RepositorioMovimientosFalso()
    app.dependency_overrides[get_movimientos_repository] = lambda: falso
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1, rol=roles.TESORERO
    )
    return falso


def movimiento(monto_debito=100.5, monto_credito=100.5, **cambios):
    datos = {
        "fecha": "2026-11-02",
        "descripcion": "Cobro de cuotas",
        "detalle": [
            {"id_cuenta": 1, "monto": monto_debito, "tipo": "DEBITO"},
            {"id_cuenta": 3, "monto": monto_credito, "tipo": "CREDITO"},
        ],
    }
    datos.update(cambios)
    return {clave: valor for clave, valor in datos.items() if valor != "OMITIR"}


def registrar(cliente, datos):
    return cliente.post("/movimientos", json=datos)


# --- DEF-007: fecha obligatoria ----------------------------------------------

def test_sin_fecha_responde_422(cliente, repo):
    assert registrar(cliente, movimiento(fecha="OMITIR")).status_code == 422
    assert repo.llamadas == []


def test_fecha_null_responde_422(cliente, repo):
    assert registrar(cliente, movimiento(fecha=None)).status_code == 422
    assert repo.llamadas == []


# --- DEF-019: resto de validaciones ------------------------------------------

def test_fecha_futura_responde_422(cliente, repo):
    manana = (hoy_en_panama() + timedelta(days=1)).isoformat()

    assert registrar(cliente, movimiento(fecha=manana)).status_code == 422
    assert repo.llamadas == []


def test_fecha_de_hoy_se_acepta(cliente, repo):
    assert registrar(cliente, movimiento(fecha=hoy_en_panama().isoformat())).status_code == 201


@pytest.mark.parametrize("descripcion", ["", "   "])
def test_descripcion_vacia_responde_422(cliente, repo, descripcion):
    assert registrar(cliente, movimiento(descripcion=descripcion)).status_code == 422


@pytest.mark.parametrize("monto", [10.005, 0.001])
def test_monto_con_mas_de_dos_decimales_responde_422(cliente, repo, monto):
    assert registrar(cliente, movimiento(monto, monto)).status_code == 422
    assert repo.llamadas == []


def test_monto_mas_grande_que_numeric_12_2_responde_422(cliente, repo):
    assert registrar(cliente, movimiento(1e13, 1e13)).status_code == 422


@pytest.mark.parametrize("monto", [0, -5])
def test_monto_cero_o_negativo_responde_422(cliente, repo, monto):
    assert registrar(cliente, movimiento(monto, monto)).status_code == 422


def test_la_partida_doble_se_compara_sin_errores_de_redondeo(cliente, repo):
    datos = movimiento()
    datos["detalle"] = [
        {"id_cuenta": 1, "monto": 0.1, "tipo": "DEBITO"},
        {"id_cuenta": 2, "monto": 0.2, "tipo": "DEBITO"},
        {"id_cuenta": 3, "monto": 0.3, "tipo": "CREDITO"},
    ]

    assert registrar(cliente, datos).status_code == 201


def test_a_la_bd_llegan_montos_numericos_y_descripcion_sin_espacios(cliente, repo):
    registrar(cliente, movimiento(9999999999.99, "9999999999.99", descripcion="  Cobro  "))

    fecha, descripcion, detalle = repo.llamadas[0]
    assert descripcion == "Cobro"
    assert [linea["monto"] for linea in detalle] == [9999999999.99, 9999999999.99]


def test_hoy_es_la_fecha_de_panama_y_no_la_del_servidor(monkeypatch):
    # 2026-11-16 02:00 UTC todavía es 2026-11-15 en Panamá (UTC-5).
    from datetime import datetime as datetime_real, timezone

    import app.schemas.movimientos as esquema

    class RelojFijo(datetime_real):
        @classmethod
        def now(cls, tz=None):
            return datetime_real(2026, 11, 16, 2, 0, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(esquema, "datetime", RelojFijo)

    assert esquema.hoy_en_panama().isoformat() == "2026-11-15"
