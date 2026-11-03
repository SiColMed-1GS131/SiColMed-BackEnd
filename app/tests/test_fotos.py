"""Pruebas de POST/GET /medicos/{id}/foto. No necesitan una base de datos."""

from unittest.mock import Mock

import pytest

from app.config import settings
from app.database import get_db
from app.main import app
from app.repositories import medicos as repositorio
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 32


@pytest.fixture
def bd(cliente, monkeypatch, tmp_path):
    """Médicos 7 y 8 existen; las rutas guardadas quedan en un diccionario."""
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path))
    guardadas = {}
    monkeypatch.setattr(repositorio, "existe_medico", lambda db, id: id in (7, 8))
    monkeypatch.setattr(repositorio, "guardar_foto", lambda db, id, ruta: guardadas.__setitem__(id, ruta))
    monkeypatch.setattr(repositorio, "obtener_foto", lambda db, id: guardadas.get(id))
    app.dependency_overrides[get_db] = lambda: Mock()
    _como(roles.MEDICO, id_medico=7)
    return guardadas


def _como(rol, id_medico=None):
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1, rol=rol, id_medico=id_medico
    )


def _subir(cliente, id_medico=7, contenido=PNG, nombre="foto.png", tipo="image/png"):
    return cliente.post(f"/medicos/{id_medico}/foto", files={"archivo": (nombre, contenido, tipo)})


def test_medico_sube_su_foto_y_se_ve_sin_sesion(cliente, bd, tmp_path):
    respuesta = _subir(cliente)

    assert respuesta.status_code == 201
    assert respuesta.json() == {"foto": "fotos/7.png", "url": "/medicos/7/foto"}
    assert (tmp_path / "fotos" / "7.png").read_bytes() == PNG

    app.dependency_overrides.pop(get_usuario_actual)
    vista = cliente.get("/medicos/7/foto")
    assert vista.status_code == 200
    assert vista.headers["content-type"] == "image/png"
    assert vista.content == PNG


def test_cambiar_de_png_a_jpg_borra_la_anterior(cliente, bd, tmp_path):
    _subir(cliente)
    respuesta = _subir(cliente, contenido=JPG, nombre="foto.jpeg", tipo="image/jpeg")

    assert respuesta.json()["foto"] == "fotos/7.jpg"
    assert (tmp_path / "fotos" / "7.jpg").exists()
    assert not (tmp_path / "fotos" / "7.png").exists()


def test_admin_puede_subir_la_de_cualquier_medico(cliente, bd):
    _como(roles.ADMIN_CMP)

    assert _subir(cliente, id_medico=8).status_code == 201


def test_medico_no_puede_subir_la_de_otro(cliente, bd):
    assert _subir(cliente, id_medico=8).status_code == 403
    assert bd == {}


@pytest.mark.parametrize("contenido, nombre, tipo, mensaje", [
    (b"texto plano renombrado", "foto.png", "image/png", "no es una imagen"),
    (JPG, "foto.png", "image/png", "no es una imagen"),          # dice PNG pero es JPG
    (PNG, "foto.gif", "image/png", "extensión"),
    (PNG, "foto.png", "image/gif", "JPG o PNG"),
])
def test_rechaza_lo_que_no_es_jpg_o_png(cliente, bd, tmp_path, contenido, nombre, tipo, mensaje):
    respuesta = _subir(cliente, contenido=contenido, nombre=nombre, tipo=tipo)

    assert respuesta.status_code == 415
    assert mensaje in respuesta.json()["detail"]
    assert bd == {}


def test_rechaza_mas_de_2_mb(cliente, bd):
    assert _subir(cliente, contenido=PNG + b"0" * (2 * 1024 * 1024)).status_code == 413


def test_ruta_fuera_de_fotos_no_se_sirve(cliente, bd, tmp_path):
    # medico.foto también se puede escribir por PATCH: no debe servir otros archivos
    (tmp_path / "certificados").mkdir()
    (tmp_path / "certificados" / "7.pdf").write_bytes(b"%PDF-")
    bd[7] = "certificados/7.pdf"

    assert cliente.get("/medicos/7/foto").status_code == 404


def test_sin_foto_devuelve_404(cliente, bd):
    assert cliente.get("/medicos/7/foto").status_code == 404
