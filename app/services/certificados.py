"""Certificado de idoneidad en PDF de cada médico.

Hay un archivo por médico: <UPLOADS_DIR>/certificados/<id_medico>.pdf. Subir uno
nuevo reemplaza el anterior. En medico.certificado_pdf se guarda la ruta
relativa a UPLOADS_DIR (por ejemplo "certificados/7.pdf").
"""

import os
import tempfile
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.repositories import medicos as repository

TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB
_FIRMA_PDF = b"%PDF-"
_TAMANO_BLOQUE = 64 * 1024


class CertificadoInvalido(ValueError):
    """El archivo no es un PDF aceptable (mensaje listo para el usuario)."""


class CertificadoDemasiadoGrande(CertificadoInvalido):
    pass


class MedicoSinRegistro(LookupError):
    pass


def _carpeta() -> Path:
    return Path(settings.uploads_dir).resolve()


def ruta_relativa(id_medico: int) -> str:
    return f"certificados/{id_medico}.pdf"


async def _leer_pdf(archivo: UploadFile) -> bytes:
    """Lee el archivo validando extensión, tipo MIME, tamaño y contenido."""
    nombre = (archivo.filename or "").lower()
    if not nombre.endswith(".pdf"):
        raise CertificadoInvalido("El certificado debe ser un archivo con extensión .pdf.")
    if (archivo.content_type or "").lower() != "application/pdf":
        raise CertificadoInvalido("El certificado debe enviarse con tipo application/pdf.")

    contenido = bytearray()
    while bloque := await archivo.read(_TAMANO_BLOQUE):
        contenido += bloque
        if len(contenido) > TAMANO_MAXIMO:
            raise CertificadoDemasiadoGrande("El certificado no puede superar 5 MB.")

    # La extensión y el tipo MIME los decide quien envía: el contenido manda.
    if not contenido.startswith(_FIRMA_PDF):
        raise CertificadoInvalido("El archivo no es un PDF válido.")
    return bytes(contenido)


async def guardar_certificado(db: Session, id_medico: int, archivo: UploadFile) -> str:
    """Valida y guarda el PDF, y registra su ruta en el médico. Devuelve la ruta relativa."""
    if not repository.existe_medico(db, id_medico):
        raise MedicoSinRegistro(f"No existe el médico {id_medico}")
    contenido = await _leer_pdf(archivo)

    relativa = ruta_relativa(id_medico)
    destino = _carpeta() / relativa
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Se escribe en un temporal y se renombra, para no dejar un PDF a medias
    descriptor, temporal = tempfile.mkstemp(dir=destino.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as salida:
            salida.write(contenido)
        os.replace(temporal, destino)
    except BaseException:
        Path(temporal).unlink(missing_ok=True)
        raise

    repository.guardar_certificado_pdf(db, id_medico, relativa)
    return relativa


def ruta_certificado(db: Session, id_medico: int) -> Path | None:
    """Ruta física del PDF del médico, o None si no tiene uno guardado."""
    relativa = repository.obtener_certificado_pdf(db, id_medico)
    if not relativa:
        return None
    carpeta = _carpeta()
    ruta = (carpeta / relativa).resolve()
    if not ruta.is_relative_to(carpeta) or not ruta.is_file():
        return None
    return ruta
