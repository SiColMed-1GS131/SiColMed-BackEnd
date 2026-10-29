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
from pwdlib import PasswordHash
from sqlalchemy.exc import DBAPIError

from app.repositories.auth import AuthRepository, get_auth_repository
from app.schemas.auth import (
    LoginSolicitud,
    RegistroSolicitud,
    TokenRespuesta,
    UsuarioRespuesta,
)
from app.security import roles
from app.security.jwt import crear_token_acceso

class CredencialesInvalidas(Exception):
    pass


class UsuarioInactivo(Exception):
    pass


class UsuarioNoEncontrado(Exception):
    pass


class MedicoNoEncontrado(Exception):
    pass


class CuentaYaRegistrada(Exception):
    pass


_hasher = PasswordHash.recommended()
_hash_relleno = _hasher.hash("contraseña-no-válida-para-login")


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
        password_hash = _hasher.hash(datos.password)
        try:
            id_usuario = self.repositorio.crear_cuenta_medico(
                datos.numero_idoneidad,
                str(datos.correo),
                password_hash,
            )
        except DBAPIError as error:
            diagnostico = getattr(getattr(error, "orig", None), "diag", None)
            mensaje = str(
                getattr(diagnostico, "message_primary", None)
                or getattr(error, "orig", error)
            ).lower()
            if "no existe un médico" in mensaje:
                raise MedicoNoEncontrado from error
            if "ya tiene una cuenta" in mensaje or "ya está registrado" in mensaje:
                raise CuentaYaRegistrada from error
            raise
        return TokenRespuesta(
            access_token=crear_token_acceso(id_usuario, roles.MEDICO)
        )

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
        fila = self.repositorio.obtener_credenciales_usuario(str(datos.username))
        hash_guardado = fila["password_hash"] if fila else _hash_relleno
        password_valida = _hasher.verify(datos.password, hash_guardado)
        if not fila or not password_valida:
            raise CredencialesInvalidas
        if not fila["activo"]:
            raise UsuarioInactivo
        return TokenRespuesta(
            access_token=crear_token_acceso(fila["id_usuario"], fila["rol"])
        )

    def obtener_usuario(self, id_usuario: int) -> UsuarioRespuesta:
        """GET /auth/me. El token ya viene validado por get_usuario_actual.

        TODO:
        1. fila = repositorio.obtener_usuario_por_id(id_usuario).
        2. Sin fila → 401; activo false → 403.
        3. Construir UsuarioRespuesta con el mapeo de nombres de app/schemas/auth.py.
        """
        fila = self.repositorio.obtener_usuario_por_id(id_usuario)
        if fila is None:
            raise UsuarioNoEncontrado
        if not fila["activo"]:
            raise UsuarioInactivo
        return UsuarioRespuesta(
            id=fila["id_usuario"],
            username=fila["correo"],
            nombre=fila["nombre"],
            email=fila["correo"],
            idoneidad=fila["numero_idoneidad"],
            role=fila["rol"],
            is_active=fila["activo"],
        )


def get_auth_service(
    repositorio: AuthRepository = Depends(get_auth_repository),
) -> AuthService:
    return AuthService(repositorio)
