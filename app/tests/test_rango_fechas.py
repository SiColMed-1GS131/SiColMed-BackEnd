"""DEF-012: un rango de fechas invertido respondía 500.

Criterio: 422 con el mensaje "La fecha de inicio no puede ser posterior a la fecha de
fin", en el balance general y en los movimientos por cuenta.
"""

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.repositories.movimientos import get_movimientos_repository
from app.repositories.reportes import get_reportes_repository
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado

MENSAJE = "La fecha de inicio no puede ser posterior a la fecha de fin"
RUTAS = ["/cuentas/1/movimientos", "/reportes/balance-general"]


class RepositorioFalso:
    def consultar_por_cuenta(self, id_cuenta, fecha_inicio, fecha_fin):
        return []

    def balance_general(self, fecha_inicio, fecha_fin):
        return []

    def tipos_de_cuenta(self):
        return {}


@pytest.fixture
def cliente_sin_excepciones():
    # raise_server_exceptions=False: así un error no controlado se ve como el 500 real.
    falso = RepositorioFalso()
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_movimientos_repository] = lambda: falso
    app.dependency_overrides[get_reportes_repository] = lambda: falso
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1, rol=roles.ADMIN_CMP
    )
    with TestClient(app, raise_server_exceptions=False) as cliente:
        yield cliente
    app.dependency_overrides.clear()


@pytest.mark.parametrize("ruta", RUTAS)
def test_rango_invertido_responde_422_con_mensaje(cliente_sin_excepciones, ruta):
    respuesta = cliente_sin_excepciones.get(
        ruta, params={"fecha_inicio": "2026-12-31", "fecha_fin": "2026-01-01"}
    )

    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": MENSAJE}


@pytest.mark.parametrize("ruta", RUTAS)
def test_rango_valido_y_de_un_solo_dia_responden_200(cliente_sin_excepciones, ruta):
    for fin in ("2026-12-31", "2026-01-01"):
        respuesta = cliente_sin_excepciones.get(
            ruta, params={"fecha_inicio": "2026-01-01", "fecha_fin": fin}
        )
        assert respuesta.status_code == 200


@pytest.mark.parametrize("ruta", RUTAS)
def test_sin_fecha_fin_sigue_respondiendo_422(cliente_sin_excepciones, ruta):
    respuesta = cliente_sin_excepciones.get(ruta, params={"fecha_inicio": "2026-01-01"})

    assert respuesta.status_code == 422
