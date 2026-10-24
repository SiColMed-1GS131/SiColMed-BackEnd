from pathlib import Path
import re

from sqlalchemy import create_engine

from alembic_utils.pg_function import PGFunction
from app.config import settings


DIRECTORIO_FUNCIONES = Path(__file__).parent


def cargar_funciones():
    funciones = []

    # Obtener las firmas que PostgreSQL ya reconoce.
    engine = create_engine(settings.database_url)

    try:
        with engine.connect() as conexion:
            funciones_bd = PGFunction.from_database(
                conexion,
                schema="public",
            )
    finally:
        engine.dispose()

    firmas_bd = {
        funcion.signature.split("(", 1)[0].strip().lower(): funcion.signature
        for funcion in funciones_bd
    }

    for ruta in sorted(DIRECTORIO_FUNCIONES.glob("*.sql")):
        sql = ruta.read_text(encoding="utf-8").strip()

        # Eliminar comentarios completos al principio del archivo.
        sql = re.sub(
            r"\A(?:\s*--[^\n]*(?:\n|$))*\s*",
            "",
            sql,
        )

        # Extraer el nombre de la función y su definición.
        coincidencia = re.match(
            r"(?is)^CREATE\s+OR\s+REPLACE\s+FUNCTION\s+"
            r"(?:public\s*\.\s*)?"
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*"
            r"\(.*?\)\s*(RETURNS\b.*)$",
            sql,
        )

        if not coincidencia:
            raise RuntimeError(
                f"No se pudo identificar la función en {ruta.name}"
            )

        nombre = coincidencia.group(1)
        definicion = coincidencia.group(2).strip()

        firma = firmas_bd.get(nombre.lower())

        if firma is None:
            raise RuntimeError(
                f"No se encontró la firma de {nombre} en PostgreSQL. "
                "No se registrará automáticamente una función nueva "
                "sin determinar antes su firma."
            )

        funciones.append(
            PGFunction(
                schema="public",
                signature=firma,
                definition=definicion,
            )
        )

    return funciones
