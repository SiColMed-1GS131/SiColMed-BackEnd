"""DEF-006: bloqueo de la cuenta tras 5 intentos fallidos de login.

Criterio: al sexto intento tras 5 fallos consecutivos, POST /auth/login responde
429 durante 5 minutos aunque la contraseña sea correcta, y cada intento (éxito o
fallo) queda registrado en log_inicio_sesion.

El repositorio falso guarda el log en memoria y simula el reloj de la BD con
`ahora` (en segundos), así las pruebas no esperan minutos reales.
"""

import pytest

from app.config import settings
from app.repositories.auth import get_auth_repository
from app.main import app
from app.services.auth import (
    MAX_INTENTOS_FALLIDOS,
    SEGUNDOS_DE_BLOQUEO,
    _hasher,
    segundos_de_bloqueo,
)

CORREO = "medico.bloqueo@colmed.dev"
CLAVE_CORRECTA = "ClaveCorrecta123!"
ID_USUARIO = 7


class RepoAuthFalso:
    def __init__(self):
        self.ahora = 1_000_000
        self.activo = True
        self.log: list[tuple[int, str, int]] = []  # (id_usuario, resultado, momento)
        self._hash = _hasher.hash(CLAVE_CORRECTA)

    def obtener_credenciales_usuario(self, correo):
        if correo.lower() != CORREO:
            return None
        return {
            "id_usuario": ID_USUARIO,
            "correo": CORREO,
            "password_hash": self._hash,
            "rol": "medico",
            "activo": self.activo,
        }

    def listar_intentos_inicio_sesion(self, id_usuario, limite):
        filas = [
            {"resultado": resultado, "segundos_transcurridos": self.ahora - momento}
            for usuario, resultado, momento in reversed(self.log)
            if usuario == id_usuario
        ]
        return filas[:limite]

    def registrar_intento_inicio_sesion(self, id_usuario, exitoso):
        self.log.append((id_usuario, "EXITOSO" if exitoso else "FALLIDO", self.ahora))
        return len(self.log)

    def obtener_id_medico(self, id_usuario):
        return 3

    @property
    def resultados(self):
        return [resultado for _, resultado, _ in self.log]


@pytest.fixture
def repo(cliente, monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret_key", "clave-de-pruebas-" * 4)
    falso = RepoAuthFalso()
    app.dependency_overrides[get_auth_repository] = lambda: falso
    return falso


def iniciar_sesion(cliente, clave, correo=CORREO):
    return cliente.post("/auth/login", json={"username": correo, "password": clave})


def fallar(cliente, repo, veces, separacion=10):
    for _ in range(veces):
        assert iniciar_sesion(cliente, "ClaveEquivocada1!").status_code == 401
        repo.ahora += separacion


# --- Reglas del bloqueo (función pura) --------------------------------------

def fallo(hace):
    return {"resultado": "FALLIDO", "segundos_transcurridos": hace}


def exito(hace):
    return {"resultado": "EXITOSO", "segundos_transcurridos": hace}


def test_sin_intentos_no_hay_bloqueo():
    assert segundos_de_bloqueo([]) == 0


def test_cuatro_fallos_no_bloquean():
    assert segundos_de_bloqueo([fallo(s) for s in (1, 2, 3, 4)]) == 0


def test_cinco_fallos_seguidos_bloquean_cinco_minutos_desde_el_ultimo():
    assert segundos_de_bloqueo([fallo(s) for s in (10, 20, 30, 40, 50)]) == SEGUNDOS_DE_BLOQUEO - 10


def test_cinco_fallos_aunque_esten_separados_en_el_tiempo_bloquean():
    # "Consecutivos" = sin un inicio exitoso en medio, no "en poco tiempo".
    intentos = [fallo(s) for s in (5, 3600, 7200, 10800, 14400)]
    assert segundos_de_bloqueo(intentos) == SEGUNDOS_DE_BLOQUEO - 5


def test_el_bloqueo_vence_a_los_cinco_minutos():
    hace = SEGUNDOS_DE_BLOQUEO
    assert segundos_de_bloqueo([fallo(hace + s) for s in (0, 1, 2, 3, 4)]) == 0


def test_un_inicio_exitoso_reinicia_la_cuenta_de_fallos():
    intentos = [fallo(1), fallo(2), exito(3), fallo(4), fallo(5), fallo(6), fallo(7)]
    assert segundos_de_bloqueo(intentos) == 0


def test_los_intentos_durante_el_bloqueo_no_lo_alargan():
    # 5 fallos hace 200 s (bloqueo hasta dentro de 100 s) y 10 intentos más durante el bloqueo.
    intentos = [fallo(s) for s in range(110, 200, 10)] + [fallo(200 + s) for s in range(5)]
    assert segundos_de_bloqueo(intentos) == SEGUNDOS_DE_BLOQUEO - 200


def test_tras_vencer_el_bloqueo_un_fallo_mas_no_vuelve_a_bloquear():
    vencido = SEGUNDOS_DE_BLOQUEO + 60
    intentos = [fallo(5)] + [fallo(vencido + s) for s in range(5)]
    assert segundos_de_bloqueo(intentos) == 0


# --- POST /auth/login --------------------------------------------------------

def test_sexto_intento_con_la_clave_correcta_responde_429(cliente, repo):
    fallar(cliente, repo, MAX_INTENTOS_FALLIDOS)

    respuesta = iniciar_sesion(cliente, CLAVE_CORRECTA)

    assert respuesta.status_code == 429
    assert int(respuesta.headers["Retry-After"]) > 0
    assert "bloqueada" in respuesta.json()["detail"]
    assert "access_token" not in respuesta.json()


def test_el_bloqueo_dura_cinco_minutos_y_luego_deja_entrar(cliente, repo):
    fallar(cliente, repo, MAX_INTENTOS_FALLIDOS)
    repo.ahora += SEGUNDOS_DE_BLOQUEO - 60
    assert iniciar_sesion(cliente, CLAVE_CORRECTA).status_code == 429

    repo.ahora += 60
    respuesta = iniciar_sesion(cliente, CLAVE_CORRECTA)

    assert respuesta.status_code == 200
    assert respuesta.json()["access_token"]


def test_cuatro_fallos_y_la_clave_correcta_inicia_sesion(cliente, repo):
    fallar(cliente, repo, MAX_INTENTOS_FALLIDOS - 1)

    assert iniciar_sesion(cliente, CLAVE_CORRECTA).status_code == 200


def test_cada_intento_queda_registrado_en_el_log(cliente, repo):
    fallar(cliente, repo, MAX_INTENTOS_FALLIDOS)
    iniciar_sesion(cliente, CLAVE_CORRECTA)  # bloqueado: también se registra
    repo.ahora += SEGUNDOS_DE_BLOQUEO
    iniciar_sesion(cliente, CLAVE_CORRECTA)

    assert repo.resultados == ["FALLIDO"] * (MAX_INTENTOS_FALLIDOS + 1) + ["EXITOSO"]


def test_usuario_inactivo_registra_un_intento_fallido(cliente, repo):
    repo.activo = False

    assert iniciar_sesion(cliente, CLAVE_CORRECTA).status_code == 403
    assert repo.resultados == ["FALLIDO"]


def test_correo_inexistente_responde_401_sin_registrar_nada(cliente, repo):
    respuesta = iniciar_sesion(cliente, CLAVE_CORRECTA, correo="nadie@colmed.dev")

    assert respuesta.status_code == 401
    assert repo.log == []
