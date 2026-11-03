"""Certificado de idoneidad en PDF de cada médico.

Hay un archivo por médico: <UPLOADS_DIR>/certificados/<id_medico>.pdf. Subir uno
nuevo reemplaza el anterior. En medico.certificado_pdf se guarda la ruta
relativa a UPLOADS_DIR (por ejemplo "certificados/7.pdf").
"""

from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.repositories import medicos as repository
from app.services import archivos

TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB
_FIRMA_PDF = b"%PDF-"


class CertificadoInvalido(ValueError):
    """El archivo no es un PDF aceptable (mensaje listo para el usuario)."""


class CertificadoDemasiadoGrande(CertificadoInvalido):
    pass


class MedicoSinRegistro(LookupError):
    pass


def ruta_relativa(id_medico: int) -> str:
    return f"certificados/{id_medico}.pdf"


async def _leer_pdf(archivo: UploadFile) -> bytes:
    """Lee el archivo validando extensión, tipo MIME, tamaño y contenido."""
    nombre = (archivo.filename or "").lower()
    if not nombre.endswith(".pdf"):
        raise CertificadoInvalido("El certificado debe ser un archivo con extensión .pdf.")
    if (archivo.content_type or "").lower() != "application/pdf":
        raise CertificadoInvalido("El certificado debe enviarse con tipo application/pdf.")

    try:
        contenido = await archivos.leer_con_limite(
            archivo, TAMANO_MAXIMO, "El certificado no puede superar 5 MB."
        )
    except archivos.ArchivoDemasiadoGrande as error:
        raise CertificadoDemasiadoGrande(str(error)) from error

    # La extensión y el tipo MIME los decide quien envía: el contenido manda.
    if not contenido.startswith(_FIRMA_PDF):
        raise CertificadoInvalido("El archivo no es un PDF válido.")
    return contenido


async def guardar_certificado(db: Session, id_medico: int, archivo: UploadFile) -> str:
    """Valida y guarda el PDF, y registra su ruta en el médico. Devuelve la ruta relativa."""
    if not repository.existe_medico(db, id_medico):
        raise MedicoSinRegistro(f"No existe el médico {id_medico}")
    contenido = await _leer_pdf(archivo)

    relativa = ruta_relativa(id_medico)
    archivos.guardar_atomico(relativa, contenido)
    repository.guardar_certificado_pdf(db, id_medico, relativa)
    return relativa


def ruta_certificado(db: Session, id_medico: int) -> Path | None:
    """Ruta física del PDF del médico, o None si no tiene uno guardado."""
    return archivos.ruta_existente(repository.obtener_certificado_pdf(db, id_medico), "certificados")
