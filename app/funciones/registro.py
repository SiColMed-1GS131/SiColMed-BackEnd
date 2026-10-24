from pathlib import Path

from alembic_utils.pg_function import PGFunction


CARPETA_FUNCIONES = Path(__file__).resolve().parent


def cargar_funciones():
    funciones = []

    for archivo in sorted(CARPETA_FUNCIONES.glob("*.sql")):
        sql = archivo.read_text(encoding="utf-8").strip()

        if not sql:
            continue

        if "CREATE OR REPLACE FUNCTION" not in sql.upper():
            continue

        funcion = PGFunction.from_sql(sql)
        funciones.append(funcion)

    return funciones


FUNCIONES_SQL = cargar_funciones()
