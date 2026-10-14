"""Utilidades para llamar funciones almacenadas de PostgreSQL.
 
Cada repositorio utiliza estas utilidades en lugar de escribir sentencias
SELECT manualmente, de modo que el manejo de NULL, JSON y las transacciones
se encuentran en un solo lugar.
 
Ejemplos. Los nombres de las funciones de la base de datos
(registrar_medico, filtrar_medicos...) provienen de la documentación del
equipo de base de datos y se mantienen en español. Las claves del diccionario
son únicamente nombres de parámetros vinculados: lo importante es su ORDEN.
 
    # Función que devuelve un único valor (entero, booleano, texto o json)
    doctor_id = llamar_escalar(
        db,
        "registrar_medico",
        {"license_number": "123", "national_id": "8-123-456"},
        commit=True,  # es una escritura
    )
 
    # Función que devuelve una tabla (varias filas)
    rows = llamar_tabla(
        db,
        "filtrar_medicos",
        {
            "last_name": Arg("Perez", "text"),
            "specialty_id": Arg(None, "integer"),  # NULL con un tipo explícito
        },
    )
 
    # Parámetro JSON: pasa el diccionario o la lista y se serializará automáticamente
    llamar_escalar(
        db,
        "crear_solicitud_cambio",
        {"doctor_id": Arg(10, "integer"), "changes": Arg(changes, "jsonb")},
        commit=True,
    )
 
IMPORTANT: arguments are sent by POSITION, in dictionary order. That order must
match the function signature in the DB documentation.
"""
 
import json
import re
from typing import Any, Callable, NamedTuple
 
from sqlalchemy import text
from sqlalchemy.orm import Session
 
_IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")
_SQL_TYPE = re.compile(r"^[a-z][a-z0-9_ ]*(\(\d+(,\s*\d+)?\))?(\[\])?$")
_JSON_TYPES = {"json", "jsonb"}
 
 
class Arg(NamedTuple):
    """Argumento con un tipo SQL explícito (enviado como CAST(:value AS sql_type)).
 
    Úsalo cuando el valor pueda ser None (para que PostgreSQL conozca el tipo
    de NULL) y siempre para parámetros JSON ("json" o "jsonb").
    """
 
    value: Any
    sql_type: str | None = None
 
 
def _validar_identificador(value: str, kind: str) -> None:
    if not _IDENTIFIER.match(value):
        raise ValueError(f"Invalid {kind} name: {value!r}")
 
 
def _construir_llamada(
    function: str, params: dict[str, Any] | None
) -> tuple[str, dict[str, Any]]:
    """Construye el texto de la llamada, por ejemplo f(:a, CAST(:b AS integer)).
 
    El nombre de la función, los nombres de los parámetros y los tipos se
    validan porque se incorporan al texto SQL. Los VALORES siempre viajan como
    parámetros vinculados, nunca dentro del texto.
    """
    _validar_identificador(function, "function")
 
    placeholders: list[str] = []
    values: dict[str, Any] = {}
 
    for name, arg in (params or {}).items():
        _validar_identificador(name, "parameter")
        value, sql_type = (
            (arg.value, arg.sql_type) if isinstance(arg, Arg) else (arg, None)
        )
 
        if sql_type is None:
            placeholders.append(f":{name}")
        else:
            sql_type = sql_type.strip().lower()
            if not _SQL_TYPE.match(sql_type):
                raise ValueError(f"Invalid SQL type: {sql_type!r}")
            if sql_type in _JSON_TYPES and value is not None and not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False, default=str)
            placeholders.append(f"CAST(:{name} AS {sql_type})")
 
        values[name] = value
 
    return f"{function}({', '.join(placeholders)})", values
 
 
def _ejecutar(
    db: Session,
    sql: str,
    values: dict[str, Any],
    read: Callable[[Any], Any],
    commit: bool,
) -> Any:
    try:
        result = read(db.execute(text(sql), values))
        if commit:
            db.commit()
        return result
    except Exception:
        db.rollback()
        raise
 
 
def llamar_escalar(
    db: Session,
    function: str,
    params: dict[str, Any] | None = None,
    *,
    commit: bool = False,
) -> Any:
    """Llama una función que devuelve UN valor (entero, booleano, texto o json).
 
    Si devuelve json/jsonb, el resultado llega como un diccionario o una lista
    de Python. Usa commit=True para las funciones que escriben datos.
    """
    call, values = _construir_llamada(function, params)
    return _ejecutar(db, f"SELECT {call}", values, lambda r: r.scalar_one(), commit)
 
 
def llamar_tabla(
    db: Session,
    function: str,
    params: dict[str, Any] | None = None,
    *,
    commit: bool = False,
) -> list[dict[str, Any]]:
    """Llama una función que devuelve una TABLE (RETURNS TABLE).
 
    Devuelve una lista de diccionarios, uno por fila, cuyas claves son los
    nombres de las columnas.
    """
    call, values = _construir_llamada(function, params)
    return _ejecutar(
        db,
        f"SELECT * FROM {call}",
        values,
        lambda r: [dict(row) for row in r.mappings().all()],
        commit,
    )