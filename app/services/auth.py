"""Casos de uso de autenticación; hashes Argon2 y JWT existentes."""
from fastapi import Depends
from pwdlib import PasswordHash
from app.repositories.auth import AuthRepository, get_auth_repository
from app.schemas.auth import LoginSolicitud, RegistroSolicitud, TokenRespuesta, UsuarioRespuesta
from app.security.jwt import crear_token_acceso

_hasher = PasswordHash.recommended()
# Evita una diferencia grande de tiempos entre correo existente/inexistente.
_DUMMY_HASH = _hasher.hash("relleno-no-utilizar-como-credencial")

class CredencialesInvalidas(Exception): pass
class UsuarioInactivo(Exception): pass
class UsuarioNoEncontrado(Exception): pass

class AuthService:
    def __init__(self, repositorio: AuthRepository):
        self.repositorio = repositorio

    def registrar(self, datos: RegistroSolicitud) -> TokenRespuesta:
        identificador = self.repositorio.crear_cuenta_medico(
            datos.numero_idoneidad.strip(), str(datos.correo).lower(), _hasher.hash(datos.password)
        )
        # Confirmar rol real desde DB en lugar de asumir su capitalización.
        cuenta = self.repositorio.obtener_usuario_por_id(identificador)
        if not cuenta or not cuenta["activo"]:
            raise UsuarioNoEncontrado()
        return TokenRespuesta(access_token=crear_token_acceso(identificador, str(cuenta["rol"])))

    def login(self, datos: LoginSolicitud) -> TokenRespuesta:
        fila = self.repositorio.obtener_credenciales_usuario(datos.username.strip().lower())
        password_hash = str(fila.get("password_hash") or _DUMMY_HASH) if fila else _DUMMY_HASH
        try:
            coincide = _hasher.verify(datos.password, password_hash)
        except (ValueError, TypeError):
            coincide = False
        if not fila or not coincide:
            raise CredencialesInvalidas()
        if not fila["activo"]:
            raise UsuarioInactivo()
        return TokenRespuesta(access_token=crear_token_acceso(int(fila["id_usuario"]), str(fila["rol"])))

    def obtener_usuario(self, id_usuario: int) -> UsuarioRespuesta:
        fila = self.repositorio.obtener_usuario_por_id(id_usuario)
        if not fila:
            raise UsuarioNoEncontrado()
        if not fila["activo"]:
            raise UsuarioInactivo()
        return UsuarioRespuesta(id=int(fila["id_usuario"]), username=str(fila["correo"]),
            nombre=fila.get("nombre"), email=str(fila["correo"]),
            idoneidad=fila.get("numero_idoneidad"), role=str(fila["rol"]), is_active=True)

def get_auth_service(repositorio: AuthRepository = Depends(get_auth_repository)) -> AuthService:
    return AuthService(repositorio)
