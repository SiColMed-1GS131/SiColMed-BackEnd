"""Pruebas de las cuentas contables (Módulo 5). No necesitan una base de datos."""

from types import SimpleNamespace

import pytest
from sqlalchemy.exc import DBAPIError

from app.main import app
from app.repositories.cuentas import CuentasRepository, get_cuentas_repository

CUENTA_VALIDA = {"nombre": "Caja general", "tipo": "DEBITO", "activa": True}


def error_bd(mensaje: str) -> DBAPIError:
    """Simula un RAISE EXCEPTION de PostgreSQL."""
    original = RuntimeError(mensaje)
    original.diag = SimpleNamespace(message_primary=mensaje)
    return DBAPIError("SELECT f()", {}, original, False)


class RepositorioCuentasFalso:
    """Reemplaza CuentasRepository: guarda las llamadas y devuelve respuestas fijas."""

    def __init__(self):
        self.llamadas = []
        self.error = None
        self.filas = [
            {"id_cuenta": 1, "nombre": "Caja general", "tipo": "DEBITO", "activa": True},
            {"id_cuenta": 2, "nombre": "Cuotas por cobrar", "tipo": "CREDITO", "activa": False},
        ]
        self.id_creado = 7
        self.editada = True
        self.resultado_eliminar = "ELIMINADA"

    def _registrar(self, *llamada):
        self.llamadas.append(llamada)
        if self.error:
            raise self.error

    def listar(self, activa):
        self._registrar("listar", activa)
        return self.filas

    def crear(self, nombre, tipo):
        self._registrar("crear", nombre, tipo)
        return self.id_creado

    def editar(self, id_cuenta, nombre, tipo, activa):
        self._registrar("editar", id_cuenta, nombre, tipo, activa)
        return self.editada

    def eliminar(self, id_cuenta):
        self._registrar("eliminar", id_cuenta)
        return self.resultado_eliminar


@pytest.fixture
def repo(cliente):
    falso = RepositorioCuentasFalso()
    app.dependency_overrides[get_cuentas_repository] = lambda: falso
    return falso


# --- GET /cuentas -----------------------------------------------------------


def test_listar_devuelve_todas_las_cuentas(cliente, repo):
    respuesta = cliente.get("/cuentas")

    assert respuesta.status_code == 200
    assert respuesta.json() == repo.filas
    assert repo.llamadas == [("listar", None)]


@pytest.mark.parametrize("valor, esperado", [("true", True), ("false", False)])
def test_listar_filtra_por_estado(cliente, repo, valor, esperado):
    respuesta = cliente.get("/cuentas", params={"activa": valor})

    assert respuesta.status_code == 200
    assert repo.llamadas == [("listar", esperado)]


def test_listar_sin_cuentas_devuelve_lista_vacia(cliente, repo):
    repo.filas = []

    respuesta = cliente.get("/cuentas")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_listar_rechaza_estado_invalido(cliente, repo):
    assert cliente.get("/cuentas", params={"activa": "quizas"}).status_code == 422
    assert repo.llamadas == []


# --- POST /cuentas ----------------------------------------------------------


def test_crear_cuenta(cliente, repo):
    respuesta = cliente.post("/cuentas", json={"nombre": "Caja general", "tipo": "DEBITO"})

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "id_cuenta": 7,
        "nombre": "Caja general",
        "tipo": "DEBITO",
        "activa": True,
    }
    assert repo.llamadas == [("crear", "Caja general", "DEBITO")]
    # A la BD llega texto simple, no el Enum de Pydantic.
    assert type(repo.llamadas[0][2]) is str


def test_crear_quita_espacios_del_nombre(cliente, repo):
    cliente.post("/cuentas", json={"nombre": "  Banco nacional  ", "tipo": "CREDITO"})

    assert repo.llamadas == [("crear", "Banco nacional", "CREDITO")]


@pytest.mark.parametrize(
    "cuerpo",
    [
        pytest.param({"tipo": "DEBITO"}, id="sin-nombre"),
        pytest.param({"nombre": "Caja"}, id="sin-tipo"),
        pytest.param({"nombre": "   ", "tipo": "DEBITO"}, id="nombre-vacio"),
        pytest.param({"nombre": "x" * 101, "tipo": "DEBITO"}, id="nombre-muy-largo"),
        pytest.param({"nombre": "Caja", "tipo": "ACTIVO"}, id="tipo-desconocido"),
        pytest.param({"nombre": "Caja", "tipo": "debito"}, id="tipo-en-minusculas"),
        pytest.param({"nombre": "Caja", "tipo": "DEBITO", "saldo": 100}, id="campo-extra"),
    ],
)
def test_crear_rechaza_datos_invalidos(cliente, repo, cuerpo):
    assert cliente.post("/cuentas", json=cuerpo).status_code == 422
    assert repo.llamadas == []


def test_crear_muestra_el_error_de_bd(cliente, repo):
    repo.error = error_bd("El tipo de cuenta debe ser DEBITO o CREDITO")

    respuesta = cliente.post("/cuentas", json={"nombre": "Caja", "tipo": "DEBITO"})

    assert respuesta.status_code == 400
    assert respuesta.json() == {"detail": "El tipo de cuenta debe ser DEBITO o CREDITO"}


# --- PUT /cuentas/{id_cuenta} -----------------------------------------------


def test_editar_cuenta(cliente, repo):
    cuerpo = {"nombre": "Caja chica", "tipo": "DEBITO", "activa": False}

    respuesta = cliente.put("/cuentas/1", json=cuerpo)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"id_cuenta": 1, **cuerpo}
    assert repo.llamadas == [("editar", 1, "Caja chica", "DEBITO", False)]


def test_editar_cuenta_inexistente_devuelve_404(cliente, repo):
    repo.editada = False

    respuesta = cliente.put("/cuentas/99", json=CUENTA_VALIDA)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "No existe la cuenta 99"}


def test_editar_muestra_el_error_de_bd_al_cambiar_el_tipo(cliente, repo):
    repo.error = error_bd("No se puede cambiar el tipo de una cuenta con movimientos")

    respuesta = cliente.put("/cuentas/1", json={**CUENTA_VALIDA, "tipo": "CREDITO"})

    assert respuesta.status_code == 400
    assert respuesta.json() == {
        "detail": "No se puede cambiar el tipo de una cuenta con movimientos"
    }


@pytest.mark.parametrize(
    "ruta, cuerpo",
    [
        pytest.param("/cuentas/1", {"nombre": "Caja", "tipo": "DEBITO"}, id="sin-activa"),
        pytest.param("/cuentas/1", {**CUENTA_VALIDA, "activa": "talvez"}, id="activa-invalida"),
        pytest.param("/cuentas/1", {**CUENTA_VALIDA, "tipo": "ACTIVO"}, id="tipo-desconocido"),
        pytest.param("/cuentas/0", CUENTA_VALIDA, id="id-cero"),
        pytest.param("/cuentas/abc", CUENTA_VALIDA, id="id-no-numerico"),
    ],
)
def test_editar_rechaza_datos_invalidos(cliente, repo, ruta, cuerpo):
    assert cliente.put(ruta, json=cuerpo).status_code == 422
    assert repo.llamadas == []


# --- DELETE /cuentas/{id_cuenta} --------------------------------------------


@pytest.mark.parametrize("resultado", ["ELIMINADA", "DESACTIVADA"])
def test_eliminar_cuenta_devuelve_el_resultado_de_bd(cliente, repo, resultado):
    repo.resultado_eliminar = resultado

    respuesta = cliente.delete("/cuentas/3")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"id_cuenta": 3, "resultado": resultado}
    assert repo.llamadas == [("eliminar", 3)]


def test_eliminar_muestra_el_error_de_bd(cliente, repo):
    repo.error = error_bd("La cuenta 99 no existe")

    respuesta = cliente.delete("/cuentas/99")

    assert respuesta.status_code == 400
    assert respuesta.json() == {"detail": "La cuenta 99 no existe"}


@pytest.mark.parametrize("ruta", ["/cuentas/0", "/cuentas/-1", "/cuentas/abc"])
def test_eliminar_rechaza_id_invalido(cliente, repo, ruta):
    assert cliente.delete(ruta).status_code == 422
    assert repo.llamadas == []


# --- Repositorio: nombres y orden de los argumentos de BD -------------------


class BdFalsa:
    def __init__(self, resultado):
        self.resultado = resultado
        self.sql = None
        self.valores = None
        self.commits = 0

    def execute(self, sentencia, valores):
        self.sql = str(sentencia)
        self.valores = valores
        return self

    def scalar_one(self):
        return self.resultado

    def mappings(self):
        return self

    def all(self):
        return self.resultado

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


def test_repositorio_crear_llama_crear_cuenta():
    bd = BdFalsa(5)

    assert CuentasRepository(bd).crear("Caja", "DEBITO") == 5
    assert bd.sql == "SELECT crear_cuenta(CAST(:nombre AS text), CAST(:tipo AS text))"
    assert bd.valores == {"nombre": "Caja", "tipo": "DEBITO"}
    assert bd.commits == 1


def test_repositorio_editar_respeta_el_orden_de_la_firma():
    bd = BdFalsa(True)

    assert CuentasRepository(bd).editar(1, "Caja", "DEBITO", False) is True
    assert bd.sql == (
        "SELECT editar_cuenta(CAST(:id_cuenta AS integer), CAST(:nombre AS text), "
        "CAST(:tipo AS text), CAST(:activa AS boolean))"
    )
    assert bd.valores == {"id_cuenta": 1, "nombre": "Caja", "tipo": "DEBITO", "activa": False}
    assert bd.commits == 1


def test_repositorio_eliminar_llama_eliminar_cuenta():
    bd = BdFalsa("DESACTIVADA")

    assert CuentasRepository(bd).eliminar(3) == "DESACTIVADA"
    assert bd.sql == "SELECT eliminar_cuenta(CAST(:id_cuenta AS integer))"
    assert bd.commits == 1


def test_repositorio_listar_envia_null_y_no_confirma():
    bd = BdFalsa([{"id_cuenta": 1}])

    assert CuentasRepository(bd).listar(None) == [{"id_cuenta": 1}]
    assert bd.sql == "SELECT * FROM listar_cuentas(CAST(:activa AS boolean))"
    assert bd.valores == {"activa": None}
    assert bd.commits == 0
