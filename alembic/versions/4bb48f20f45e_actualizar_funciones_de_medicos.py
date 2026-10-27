from pathlib import Path
from typing import Sequence, Union

from alembic import op


revision: str = "4bb48f20f45e"
down_revision: Union[str, Sequence[str], None] = "88c353f63603"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    carpeta_funciones = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "funciones"
    )

    archivos = [
        carpeta_funciones / "filtrar_medicos.sql",
        carpeta_funciones / "actualizar_medico.sql",
    ]

    # Comprobar que ambos archivos existen antes de modificar la BD.
    for archivo in archivos:
        if not archivo.is_file():
            raise RuntimeError(
                f"No se encontró el archivo SQL: {archivo}"
            )

    # Eliminar la función anterior porque cambia de RETURNS TABLE
    # a RETURNS JSONB. La firma corresponde a la versión instalada.
    op.execute("""
        DROP FUNCTION filtrar_medicos(
            text,
            integer,
            integer,
            integer,
            boolean,
            integer,
            text,
            integer,
            integer
        );
    """)

    # Instalar las versiones actualizadas de ambas funciones.
    conexion = op.get_bind().connection
    cursor = conexion.cursor()

    try:
        for archivo in archivos:
            sql = archivo.read_text(encoding="utf-8").strip()

            if sql:
                cursor.execute(sql)
    finally:
        cursor.close()


def downgrade() -> None:
    raise NotImplementedError(
        "Para revertir esta migración es necesario restaurar "
        "las versiones anteriores de ambas funciones SQL."
    )
