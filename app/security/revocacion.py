"""Tokens cerrados con POST /auth/logout (DEF-008, parte 2).

Decisión del líder (DECISIONES_CONFIRMADAS, sección 2): lista en memoria de la API.
Se guarda la huella SHA-256 del token (nunca el token) hasta su `exp`; después el
token ya no sirve por sí solo y la entrada se descarta.

Limitación aceptada: la lista vive en el proceso de la API. Si la API se reinicia
se pierde, y los tokens cerrados vuelven a servir hasta su vencimiento (60 minutos
como máximo). Tampoco se comparte entre procesos; hoy la API corre uno solo.
"""

import hashlib
import threading
import time

import jwt

_revocados: dict[str, float] = {}  # huella del token -> exp (segundos epoch)
_candado = threading.Lock()


def _huella(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _descartar_vencidos(ahora: float) -> None:
    for huella in [h for h, exp in _revocados.items() if exp <= ahora]:
        del _revocados[huella]


def revocar_token(token: str) -> None:
    """Marca el token como cerrado hasta su exp. Se llama con un token ya validado."""
    exp = jwt.decode(token, options={"verify_signature": False}).get("exp")
    if not isinstance(exp, (int, float)):
        return
    ahora = time.time()
    with _candado:
        _descartar_vencidos(ahora)
        if exp > ahora:
            _revocados[_huella(token)] = float(exp)


def token_revocado(token: str) -> bool:
    with _candado:
        exp = _revocados.get(_huella(token))
    return exp is not None and exp > time.time()


def limpiar_revocados() -> None:
    """Solo para pruebas."""
    with _candado:
        _revocados.clear()
