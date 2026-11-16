"""DEF-003: CORS_ORIGINS con barra final bloqueaba el preflight del login.

El navegador manda `Origin: http://localhost:3000` (sin barra). Si el .env trae
`CORS_ORIGINS=http://localhost:3000/`, la comparación exacta de CORSMiddleware
fallaba y `OPTIONS /auth/login` respondía 400, así que nadie podía iniciar sesión.
"""

from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.main import app, origenes_cors

ORIGEN_WEB = "http://localhost:3000"
PREFLIGHT_LOGIN = {
    "Origin": ORIGEN_WEB,
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}


def test_origenes_cors_quita_barra_final_y_espacios():
    valor = " http://localhost:3000/ ,http://127.0.0.1:3000"

    assert origenes_cors(valor) == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_preflight_login_con_barra_final_en_la_configuracion_responde_200():
    # Misma configuración que main.py, pero con el valor que traía .env.example.
    api = CORSMiddleware(
        app,
        allow_origins=origenes_cors("http://localhost:3000/"),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    with TestClient(api) as cliente:
        respuesta = cliente.options("/auth/login", headers=PREFLIGHT_LOGIN)

    assert respuesta.status_code == 200
    assert respuesta.headers["access-control-allow-origin"] == ORIGEN_WEB


def test_preflight_login_desde_el_frontend_responde_200(cliente):
    respuesta = cliente.options("/auth/login", headers=PREFLIGHT_LOGIN)

    assert respuesta.status_code == 200
    assert respuesta.headers["access-control-allow-origin"] == ORIGEN_WEB
