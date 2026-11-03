"""Utilidades comunes para los archivos que suben los usuarios (certificados y fotos).

Todo se guarda bajo UPLOADS_DIR (el volumen `uploads` en Docker), fuera del webroot
del frontend. En la BD se guarda la ruta relativa a UPLOADS_DIR.
"""

import os
import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.config import settings

_TAMANO_BLOQUE = 64 * 1024


class ArchivoDemasiadoGrande(ValueError):
    pass


def carpeta_uploads() -> Path:
    return Path(settings.uploads_dir).resolve()


async def leer_con_limite(archivo: UploadFile, maximo: int, mensaje: str) -> bytes:
    """Lee el archivo por bloques y corta en cuanto supera `maximo` bytes."""
    contenido = bytearray()
    while bloque := await archivo.read(_TAMANO_BLOQUE):
        contenido += bloque
        if len(contenido) > maximo:
            raise ArchivoDemasiadoGrande(mensaje)
    return bytes(contenido)


def guardar_atomico(relativa: str, contenido: bytes) -> None:
    """Escribe en un temporal y lo renombra, para no dejar nunca un archivo a medias."""
    destino = carpeta_uploads() / relativa
    destino.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(dir=destino.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as salida:
            salida.write(contenido)
        os.replace(temporal, destino)
    except BaseException:
        Path(temporal).unlink(missing_ok=True)
        raise


def ruta_existente(relativa: str | None, carpeta: str) -> Path | None:
    """Ruta física de un archivo guardado, o None si no existe o se sale de UPLOADS_DIR/<carpeta>.

    El valor viene de la BD; se valida igual, porque columnas como medico.foto
    también se pueden escribir con el PATCH del médico.
    """
    if not relativa:
        return None
    base = (carpeta_uploads() / carpeta).resolve()
    ruta = (carpeta_uploads() / relativa).resolve()
    if not ruta.is_relative_to(base) or not ruta.is_file():
        return None
    return ruta
