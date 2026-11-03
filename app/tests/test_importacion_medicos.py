"""Pruebas de la carga masiva por CSV (requerimiento 9) sin PostgreSQL."""
import io
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError

from app.database import get_db
from app.main import app
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado
from app.services import importacion_medicos as imp

EJEMPLO = Path(__file__).resolve().parents[2] / "docs" / "ejemplos" / "carga_medicos_ejemplo.csv"
CORREGIMIENTOS = {"080807": 1, "040601": 2, "091001": 3, "060101": 4, "080812": 5}
ESPECIALIDADES = ["Medicina interna", "Cirugía general", "Pediatría", "Oftalmología", "Ginecología y obstetricia"]
SUBESPECIALIDADES = ["Cardiología", "Cirugía oncológica", "Neonatología", "Retina", "Medicina materno fetal"]


@pytest.fixture
def bd(monkeypatch):
    """Catálogos y repositorio falsos; guarda lo que se registraría."""
    estado = SimpleNamespace(registrados=[], cargas=[], fallar_en=set())
    monkeypatch.setattr(imp.catalogos, "ids_corregimiento_por_codigo", lambda db: CORREGIMIENTOS)
    monkeypatch.setattr(imp.catalogos, "especialidades", lambda db: [
        SimpleNamespace(id_especialidad=i, nombre=n) for i, n in enumerate(ESPECIALIDADES, 1)])
    monkeypatch.setattr(imp.catalogos, "subespecialidades", lambda db: [
        SimpleNamespace(id_subespecialidad=i, nombre=n) for i, n in enumerate(SUBESPECIALIDADES, 1)])
    monkeypatch.setattr(imp.catalogos, "asociaciones", lambda db: [])

    def registrar_medico(db, medico):
        if medico.medico.cedula in estado.fallar_en:
            orig = Exception("Ya existe un médico con la cédula " + medico.medico.cedula)
            raise DBAPIError("SELECT registrar_medico(...)", {}, orig)
        estado.registrados.append(medico)
        return len(estado.registrados)

    def registrar_carga(db, id_admin, archivo, procesados, registrados, errores):
        estado.cargas.append((id_admin, archivo, procesados, registrados, errores))
        return 77

    monkeypatch.setattr(imp.repository, "registrar_medico", registrar_medico)
    monkeypatch.setattr(imp.repository, "registrar_carga", registrar_carga)
    return estado


def _archivo(contenido: bytes, nombre: str = "carga.csv") -> UploadFile:
    return UploadFile(file=io.BytesIO(contenido), filename=nombre)


def test_ejemplo_registra_los_cinco_y_audita(bd):
    resultado = imp.importar(Mock(), _archivo(EJEMPLO.read_bytes(), "carga_medicos_ejemplo.csv"), 9)

    assert (resultado.procesados, resultado.registrados, resultado.rechazados) == (5, 5, 0)
    assert resultado.errores == [] and resultado.id_auditoria == 77
    assert bd.cargas == [(9, "carga_medicos_ejemplo.csv", 5, 5, [])]

    primero = bd.registrados[0]
    assert primero.medico.primer_nombre == "María"
    assert primero.medico.apellido_paterno == "Castillo"          # primer_apellido
    assert primero.medico.apellido_materno == "Ríos"              # segundo_apellido
    assert primero.medico.numero_idoneidad == "IDONEIDAD-0101"    # idoneidad
    assert primero.medico.telefono_residencial == "507-264-1180"  # telefono
    assert primero.medico.email_personal == "maria.castillo@colmed.dev"
    assert primero.direccion.apartado_postal == "0819-00112"
    assert primero.direccion.id_corregimiento == 1                # código 080807
    assert primero.direccion_trabajo.apartado_postal == "0816-00450"
    assert primero.estudio_medico.tipo_estudio == "Título básico"
    assert primero.especialidades.root == [1] and primero.subespecialidades.root == [1]
    # vigente se deduce de la fecha de expiración (la del 4.º médico ya venció: 2026-08-01)
    assert primero.certificacion.vigente is True
    assert bd.registrados[3].certificacion.vigente is (date(2026, 8, 1) >= date.today())


def test_filas_con_error_no_detienen_la_carga(bd):
    lineas = EJEMPLO.read_text(encoding="utf-8").splitlines()
    lineas[2] = lineas[2].replace(",040601,", ",999999,", 1)       # corregimiento inexistente
    lineas[3] = lineas[3].replace("Pediatría", "Inventada", 1)    # especialidad fuera del catálogo
    lineas[4] = lineas[4].replace("0605-00021", "", 1)            # apartado postal vacío
    bd.fallar_en.add("8-955-1077")                                # la BD la rechaza
    resultado = imp.importar(Mock(), _archivo("\n".join(lineas).encode("utf-8")), 9)

    assert (resultado.procesados, resultado.registrados) == (5, 1)
    errores = {e.fila: e.error for e in resultado.errores}
    assert "999999 no existe" in errores[3]
    assert "Inventada" in errores[4]
    assert "direccion.apartado_postal" in errores[5]
    assert "Ya existe un médico con la cédula 8-955-1077" in errores[6]
    assert bd.cargas[0][2:4] == (5, 1) and len(bd.cargas[0][4]) == 4


@pytest.mark.parametrize("contenido,nombre,status,mensaje", [
    ("cedula,primer_nombre\n8-1-1,Ana\n".encode("utf-8"), "a.csv", 422, "Faltan columnas"),
    ("cedula\n".encode("latin-1") + "José".encode("latin-1"), "a.csv", 415, "UTF-8"),
    (b"", "a.csv", 422, "vacío"),
    (b"x", "datos.xlsx", 415, ".csv"),
])
def test_archivo_invalido_se_rechaza_y_se_audita(bd, contenido, nombre, status, mensaje):
    with pytest.raises(imp.ImportacionInvalida) as error:
        imp.importar(Mock(), _archivo(contenido, nombre), 9)
    assert error.value.status_code == status and mensaje in str(error.value)
    assert len(bd.cargas) == 1
    _, archivo, procesados, registrados, errores = bd.cargas[0]
    assert (archivo, procesados, registrados) == (nombre, 0, 0)
    assert errores[0]["fila"] == 0 and mensaje in errores[0]["error"]


def test_bom_y_filas_vacias_se_toleran(bd):
    contenido = "﻿".encode("utf-8") + EJEMPLO.read_bytes() + b"\n,,,\n\n"
    assert imp.importar(Mock(), _archivo(contenido), 9).registrados == 5


def test_limite_de_filas(bd, monkeypatch):
    monkeypatch.setattr(imp, "MAXIMO_FILAS", 3)
    with pytest.raises(imp.ImportacionInvalida, match="máximo es 3"):
        imp.importar(Mock(), _archivo(EJEMPLO.read_bytes()), 9)


def test_endpoint_solo_administrador(bd):
    archivos = {"archivo": ("carga.csv", EJEMPLO.read_bytes(), "text/csv")}
    with TestClient(app) as cliente:
        assert cliente.post("/medicos/importar", files=archivos).status_code == 401
        app.dependency_overrides[get_db] = lambda: Mock()
        try:
            app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(id_usuario=5, rol=roles.MEDICO)
            assert cliente.post("/medicos/importar", files=archivos).status_code == 403
            app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(id_usuario=1, rol=roles.ADMIN_CMP)
            respuesta = cliente.post("/medicos/importar", files=archivos)
            assert respuesta.status_code == 200
            assert respuesta.json()["registrados"] == 5
            assert bd.cargas[-1][0] == 1        # id del usuario del token
            invalido = cliente.post("/medicos/importar", files={"archivo": ("a.csv", b"cedula\n1\n", "text/csv")})
            assert invalido.status_code == 422 and "Faltan columnas" in invalido.json()["detail"]
        finally:
            app.dependency_overrides.clear()
