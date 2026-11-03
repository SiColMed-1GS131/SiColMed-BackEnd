"""Pruebas de POST/GET /medicos/{id}/certificado. No necesitan una base de datos."""

from unittest.mock import Mock

import pytest

from app.config import settings
from app.database import get_db
from app.main import app
from app.repositories import medicos as repositorio
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado

PDF = b"%PDF-1.4\n1 0 obj << >> endobj\n%%EOF\n"


@pytest.fixture
def bd(cliente, monkeypatch, tmp_path):
    """Médicos 7 y 8 existen; las rutas guardadas quedan en un diccionario."""
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    guardadas = {}
    monkeypatch.setattr(repositorio, "existe_medico", lambda db, id: id in (7, 8))
    monkeypatch.setattr(repositorio, "guardar_certificado_pdf", lambda db, id, ruta: guardadas.__setitem__(id, ruta))
    monkeypatch.setattr(repositorio, "obtener_certificado_pdf", lambda db, id: guardadas.get(id))
    app.dependency_overrides[get_db] = lambda: Mock()
    _como(roles.MEDICO, id_medico=7)
    return guardadas


def _como(rol, id_medico=None):
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1, rol=rol, id_medico=id_medico
    )


def _subir(cliente, id_medico=7, contenido=PDF, nombre="cert.pdf", tipo="application/pdf"):
    return cliente.post(f"/medicos/{id_medico}/certificado", files={"archivo": (nombre, contenido, tipo)})


def test_medico_sube_y_descarga_su_certificado(cliente, bd, tmp_path):
    respuesta = _subir(cliente)

    assert respuesta.status_code == 201
    assert respuesta.json() == {"certificado_pdf": "certificados/7.pdf", "url": "/medicos/7/certificado"}
    assert bd == {7: "certificados/7.pdf"}
    assert (tmp_path / "certificados" / "7.pdf").read_bytes() == PDF

    descarga = cliente.get("/medicos/7/certificado")
    assert descarga.status_code == 200
    assert descarga.headers["content-type"] == "application/pdf"
    assert descarga.content == PDF


def test_admin_puede_subir_el_de_cualquier_medico(cliente, bd):
    _como(roles.ADMIN_CMP)

    assert _subir(cliente, id_medico=8).status_code == 201


def test_medico_no_puede_subir_ni_ver_el_de_otro(cliente, bd):
    assert _subir(cliente, id_medico=8).status_code == 403
    assert cliente.get("/medicos/8/certificado").status_code == 403
    assert bd == {}


def test_otros_roles_no_pueden_subir(cliente, bd):
    _como(roles.TESORERO)

    assert _subir(cliente).status_code == 403


@pytest.mark.parametrize("contenido, nombre, tipo, mensaje", [
    (b"texto plano renombrado", "cert.pdf", "application/pdf", "no es un PDF válido"),
    (PDF, "cert.txt", "application/pdf", "extensión .pdf"),
    (PDF, "cert.pdf", "text/plain", "application/pdf"),
])
def test_rechaza_lo_que_no_es_pdf(cliente, bd, tmp_path, contenido, nombre, tipo, mensaje):
    respuesta = _subir(cliente, contenido=contenido, nombre=nombre, tipo=tipo)

    assert respuesta.status_code == 415
    assert mensaje in respuesta.json()["detail"]
    assert bd == {}
    assert not (tmp_path / "certificados" / "7.pdf").exists()


def test_rechaza_mas_de_5_mb(cliente, bd):
    respuesta = _subir(cliente, contenido=PDF + b"0" * (5 * 1024 * 1024))

    assert respuesta.status_code == 413
    assert bd == {}


def test_medico_inexistente_devuelve_404(cliente, bd):
    _como(roles.ADMIN_CMP)

    assert _subir(cliente, id_medico=99).status_code == 404


def test_descarga_sin_certificado_devuelve_404(cliente, bd):
    assert cliente.get("/medicos/7/certificado").status_code == 404
