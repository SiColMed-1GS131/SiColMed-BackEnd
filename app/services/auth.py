"""Reglas de negocio de Login.

Ya disponible: app.security.jwt.crear_token_acceso(id_usuario, rol) firma el
token con sub, role, iat y exp.

PENDIENTE (Login y permisos): hashing con Argon2 y los tres casos de uso.
pwdlib ya está en requirements.txt:

    from pwdlib import PasswordHash

    hasher = PasswordHash.recommended()   # Argon2
    hasher.hash(password)                 # al registrar
    hasher.verify(password, hash)         # al iniciar sesión
"""

from fastapi import Depends

from app.repositories.auth import AuthRepository, get_auth_repository
from app.schemas.auth import (
    LoginSolicitud,
    RegistroSolicitud,
    TokenRespuesta,
    UsuarioRespuesta,
)

# TODO: definir aquí las excepciones que el router traduce a HTTP, por ejemplo
# CredencialesInvalidas (401), UsuarioInactivo (403), MedicoNoEncontrado (404)
# y CuentaYaRegistrada (409).


class AuthService:
    def __init__(self, repositorio: AuthRepository):
        self.repositorio = repositorio

    def registrar(self, datos: RegistroSolicitud) -> TokenRespuesta:
        """POST /auth/register.

        TODO:
        1. Hashear datos.password con Argon2.
        2. id_usuario = repositorio.crear_cuenta_medico(idoneidad, correo, hash).
        3. Devolver TokenRespuesta(access_token=crear_token_acceso(id_usuario, roles.MEDICO)).
        """
        raise NotImplementedError("Pendiente: registrar")

    def login(self, datos: LoginSolicitud) -> TokenRespuesta:
        """POST /auth/login.

        TODO:
        1. fila = repositorio.obtener_credenciales_usuario(datos.username).
        2. Si no hay fila o la contraseña no coincide → CredencialesInvalidas,
           con el mismo mensaje en ambos casos. Si no hay fila, verificar igual
           contra un hash de relleno para no revelar por el tiempo de respuesta
           que el correo no existe.
        3. Si fila["activo"] es false → UsuarioInactivo.
        4. Devolver TokenRespuesta(access_token=crear_token_acceso(fila["id_usuario"], fila["rol"])).
        Requisito del plan: bloquear 3 a 5 minutos tras 5 intentos fallidos
        (tabla LOG_INICIO_SESION); acordar con BD cómo se registra.
        """
        raise NotImplementedError("Pendiente: login")

    def obtener_usuario(self, id_usuario: int) -> UsuarioRespuesta:
        """GET /auth/me. El token ya viene validado por get_usuario_actual.

        TODO:
        1. fila = repositorio.obtener_usuario_por_id(id_usuario).
        2. Sin fila → 401; activo false → 403.
        3. Construir UsuarioRespuesta con el mapeo de nombres de app/schemas/auth.py.
        """
        raise NotImplementedError("Pendiente: obtener_usuario")


def get_auth_service(
    repositorio: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(repositorio)
