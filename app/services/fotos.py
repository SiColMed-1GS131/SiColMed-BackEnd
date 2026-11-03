"""Foto de perfil (JPG o PNG) de cada médico.

Hay un archivo por médico: <UPLOADS_DIR>/fotos/<id_medico>.<jpg|png>. Subir una
nueva reemplaza la anterior (si cambia de formato, se borra el archivo viejo).
La ruta relativa se guarda en la columna existente medico.foto.
"""

from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.repositories import medicos as repository
from app.services import archivos
from app.services.certificados import MedicoSinRegistro

TAMANO_MAXIMO = 2 * 1024 * 1024  # 2 MB

# Tipo MIME → (extensiones aceptadas, firma del contenido, extensión con que se guarda)
_FORMATOS = {
    "image/jpeg": ((".jpg", ".jpeg"), b"\xff\xd8\xff", ".jpg"),
    "image/png": ((".png",), b"\x89PNG\r\n\x1a\n", ".png"),
}
MEDIA_TYPES = {".jpg": "image/jpeg", ".png": "image/png"}

__all__ = ["FotoInvalida", "FotoDemasiadoGrande", "MedicoSinRegistro",
           "guardar_foto", "ruta_foto", "MEDIA_TYPES"]


class FotoInvalida(ValueError):
    """El archivo no es una foto aceptable (mensaje listo para el usuario)."""


class FotoDemasiadoGrande(FotoInvalida):
    pass


async def _leer_foto(archivo: UploadFile) -> tuple[bytes, str]:
    """Valida tipo, extensión, tamaño y que el contenido sea del tipo declarado.

    Devuelve el contenido y la extensión con que se guarda.
    """
    tipo = (archivo.content_type or "").lower()
    if tipo not in _FORMATOS:
        raise FotoInvalida("La foto debe ser una imagen JPG o PNG.")
    extensiones, firma, extension = _FORMATOS[tipo]
    if not (archivo.filename or "").lower().endswith(extensiones):
        raise FotoInvalida("La extensión del archivo no coincide con una imagen JPG o PNG.")

    try:
        contenido = await archivos.leer_con_limite(
            archivo, TAMANO_MAXIMO, "La foto no puede superar 2 MB."
        )
    except archivos.ArchivoDemasiadoGrande as error:
        raise FotoDemasiadoGrande(str(error)) from error

    # El contenido debe ser realmente del tipo declarado (no basta la extensión)
    if not contenido.startswith(firma):
        raise FotoInvalida("El archivo no es una imagen JPG o PNG válida.")
    return contenido, extension


async def guardar_foto(db: Session, id_medico: int, archivo: UploadFile) -> str:
    """Valida y guarda la foto, y registra su ruta en medico.foto. Devuelve la ruta relativa."""
    if not repository.existe_medico(db, id_medico):
        raise MedicoSinRegistro(f"No existe el médico {id_medico}")
    contenido, extension = await _leer_foto(archivo)

    relativa = f"fotos/{id_medico}{extension}"
    anterior = archivos.ruta_existente(repository.obtener_foto(db, id_medico), "fotos")
    archivos.guardar_atomico(relativa, contenido)
    repository.guardar_foto(db, id_medico, relativa)
    # Una foto anterior con otra extensión (png → jpg) ya no se usa
    if anterior is not None and anterior != (archivos.carpeta_uploads() / relativa).resolve():
        anterior.unlink(missing_ok=True)
    return relativa


def ruta_foto(db: Session, id_medico: int) -> Path | None:
    """Ruta física de la foto del médico, o None si no tiene una guardada."""
    return archivos.ruta_existente(repository.obtener_foto(db, id_medico), "fotos")
