"""DEF-014 y DEF-015: contrato de PATCH /medicos/{id} (decisión 4 del líder).

- Las relaciones {agregar, quitar} aceptan solo una de las dos claves: a la BD llegan
  las dos, porque actualizar_medico.sql las exige juntas.
- Se admiten lugar_trabajo, estudio_medico y certificacion; cada elemento actualiza una
  fila existente por su id y a la BD solo viajan los campos enviados.
"""

import pytest
from pydantic import ValidationError

from app.database import get_db
from app.main import app
from app.routers import medicos_directorio as router_directorio
from app.schemas.medicos_directorio import ActualizarMedicoSolicitud
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado
from app.services.medicos_directorio import actualizar_medico


class RepositorioCaptura:
    def __init__(self):
        self.datos = None

    def actualizar_medico(self, db, id_medico, id_administrador, datos):
        self.datos = datos
        return True


def enviar(**cambios):
    repo = RepositorioCaptura()
    actualizar_medico(None, 1, 15, ActualizarMedicoSolicitud(**cambios), repo)
    return repo.datos


# --- DEF-014: quitar opcional --------------------------------------------------

@pytest.mark.parametrize("seccion", ["especialidades", "subespecialidades", "asociaciones"])
def test_solo_agregar_llega_a_la_bd_con_quitar_vacio(seccion):
    assert enviar(**{seccion: {"agregar": [2]}}) == {seccion: {"agregar": [2], "quitar": []}}


def test_solo_quitar_llega_a_la_bd_con_agregar_vacio():
    assert enviar(especialidades={"quitar": [3]}) == {"especialidades": {"agregar": [], "quitar": [3]}}


# --- DEF-015: secciones nuevas -------------------------------------------------

def test_lugar_trabajo_envia_solo_los_campos_indicados():
    datos = enviar(lugar_trabajo=[{"id_lugar_trabajo": 4, "cargo": "Jefe de servicio"}])

    assert datos == {"lugar_trabajo": [{"id_lugar_trabajo": 4, "cargo": "Jefe de servicio"}]}


def test_estudio_medico_envia_fechas_como_fecha():
    datos = enviar(estudio_medico=[{"id_estudio": 7, "institucion": "UP", "fecha": "2010-12-15"}])

    assert datos["estudio_medico"][0]["fecha"].isoformat() == "2010-12-15"
    assert set(datos["estudio_medico"][0]) == {"id_estudio", "institucion", "fecha"}


def test_certificacion_viaja_como_certificaciones_que_es_la_clave_de_la_bd():
    datos = enviar(certificacion=[{"id_certificacion": 2, "puntaje": 90}])

    assert datos == {"certificaciones": [{"id_certificacion": 2, "puntaje": 90}]}


@pytest.mark.parametrize(
    "cambios",
    [
        {"lugar_trabajo": [{"cargo": "Sin id"}]},
        {"lugar_trabajo": [{"id_lugar_trabajo": 4}]},  # solo el id: nada que cambiar
        {"lugar_trabajo": []},
        {"estudio_medico": [{"id_estudio": 1, "campo_raro": "x"}]},
        {"certificacion": [{"id_certificacion": 0, "puntaje": 1}]},
        {"certificacion": [{"id_certificacion": 1, "puntaje": -1}]},
    ],
)
def test_secciones_mal_formadas_se_rechazan(cambios):
    with pytest.raises(ValidationError):
        ActualizarMedicoSolicitud(**cambios)


# --- Endpoint -------------------------------------------------------------------

@pytest.fixture
def repo_endpoint(cliente, monkeypatch):
    repo = RepositorioCaptura()
    monkeypatch.setattr(router_directorio, "repositorio", repo)
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=15, rol=roles.ADMIN_CMP
    )
    return repo


def test_patch_con_solo_agregar_responde_200(cliente, repo_endpoint):
    respuesta = cliente.patch("/medicos/1", json={"especialidades": {"agregar": [2]}})

    assert respuesta.status_code == 200
    assert repo_endpoint.datos == {"especialidades": {"agregar": [2], "quitar": []}}


def test_patch_admite_las_tres_secciones(cliente, repo_endpoint):
    respuesta = cliente.patch(
        "/medicos/1",
        json={
            "lugar_trabajo": [{"id_lugar_trabajo": 4, "cargo": "Jefe"}],
            "estudio_medico": [{"id_estudio": 7, "titulo": "Doctor en Medicina"}],
            "certificacion": [{"id_certificacion": 2, "puntaje": 90}],
        },
    )

    assert respuesta.status_code == 200
    assert set(repo_endpoint.datos) == {"lugar_trabajo", "estudio_medico", "certificaciones"}
