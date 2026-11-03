"""Carga los catálogos permanentes de SiColMed (todos los ambientes, incluido producción).

Uso (después de `alembic upgrade head`):
    docker compose exec api python -m app.scripts.seed_catalogos

Catálogos que carga, desde archivos versionados en app/scripts/datos/ (no usa Internet):
- División política de Panamá: provincias, distritos y corregimientos de la DPA 2025
  v4 de ANATI/IGNTG (datos/dpa_2025/*.csv, copia sin cambios de los originales).
  Fuentes y decisiones: docs/fuentes-division-politica-panama.md.
- Especialidades y subespecialidades reconocidas por el Consejo Técnico de Salud
  (datos/especialidades_cts.csv y datos/subespecialidades_cts.csv).
- Roles de app/security/roles.py.

Asociaciones y tipos de cuenta no se cargan: no hay fuente oficial para las
asociaciones, y los tipos de cuenta (DEBITO, CREDITO) son una regla de las funciones
crear_cuenta/editar_cuenta, no una tabla.

Es idempotente: nunca borra filas ni cambia una fila que ya tiene código oficial. Una
fila territorial sin código (por ejemplo, la "Panama" del seed antiguo) se adopta
cuando su nombre coincide (sin tildes ni mayúsculas) dentro de su unidad superior: se
le asigna el código y el nombre oficial, una sola vez.
"""

from __future__ import annotations

import csv
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.security import roles

DATOS = Path(__file__).resolve().parent / "datos"
DPA = DATOS / "dpa_2025"

ROLES = (roles.ADMIN_CMP, roles.MEDICO, roles.TESORERO, roles.ADMIN_ASOCIACION)

# Registros de la capa cartográfica que no son unidades administrativas legales y no
# deben aparecer como opción en los formularios (ver docs/fuentes-division-politica-panama.md).
CORREGIMIENTOS_AUXILIARES = {
    "010501": "Área de la Comarca Naso Tjër Di",
}

# Distrito que ANATI declara ficticio ("polígono distrital ficticio en la Comarca Kuna Yala
# [...] no obstante, esta comarca no tiene distritos": Metodología DPA 2025, 5.2.2, y
# metadatos/Distrito.xml). SÍ se carga, solo como contenedor: las tablas exigen un distrito
# para cada corregimiento y para cada dirección, y sin él no se podrían elegir los cuatro
# corregimientos reales de Guna Yala. Pendiente de decisión del equipo.
DISTRITOS_FICTICIOS_CARGADOS = {
    "1001": "Comarca Kuna Yala",
}


@dataclass(frozen=True)
class Unidad:
    codigo: str
    nombre: str
    codigo_superior: str | None = None


def normalizar(nombre: str) -> str:
    """Compara nombres sin tildes, mayúsculas ni espacios repetidos."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", nombre) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_tildes.casefold().split())


def _limpiar(nombre: str) -> str:
    return " ".join(nombre.split())


def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


def _unidades(filas: list[dict[str, str]], codigo: str, nombre: str, superior: str | None) -> list[Unidad]:
    # Una unidad aparece varias veces en el CSV: una fila por polígono (tierra, lago,
    # río). Se toma una sola vez por código y se exige que el nombre no cambie.
    unidades: dict[str, Unidad] = {}
    for fila in filas:
        unidad = Unidad(fila[codigo].strip(), _limpiar(fila[nombre]), fila[superior].strip() if superior else None)
        previa = unidades.setdefault(unidad.codigo, unidad)
        if previa != unidad:
            raise ValueError(f"El código {unidad.codigo} tiene datos distintos: {previa} / {unidad}")
    return sorted(unidades.values(), key=lambda u: u.codigo)


def leer_division_politica(carpeta: Path = DPA) -> tuple[list[Unidad], list[Unidad], list[Unidad]]:
    """Provincias, distritos y corregimientos de la DPA 2025, sin registros auxiliares."""
    provincias = _unidades(_leer_csv(carpeta / "limi_prov_a.csv"), "cod_prov", "nomb_prov", None)
    distritos = _unidades(_leer_csv(carpeta / "limi_dist_a.csv"), "cod_dist", "nomb_dist", "cod_prov")
    corregimientos = [
        c for c in _unidades(_leer_csv(carpeta / "limi_corr_a.csv"), "cod_corr", "nomb_corr", "cod_dist")
        if c.codigo not in CORREGIMIENTOS_AUXILIARES
    ]
    return provincias, distritos, corregimientos


def leer_especialidades(carpeta: Path = DATOS) -> list[str]:
    return [_limpiar(f["nombre"]) for f in _leer_csv(carpeta / "especialidades_cts.csv")]


def leer_subespecialidades(carpeta: Path = DATOS) -> list[tuple[str, str]]:
    """(subespecialidad, especialidad) de las que tienen UNA especialidad básica del catálogo.

    El modelo subespecialidad tiene una sola especialidad (id_especialidad). Las que el
    documento asocia a varias especialidades, o a otra subespecialidad, quedan fuera
    hasta que Base de Datos decida cómo representarlas (columna observacion del CSV).
    """
    return [
        (_limpiar(f["nombre"]), _limpiar(f["especialidad_catalogo"]))
        for f in _leer_csv(carpeta / "subespecialidades_cts.csv")
        if f["especialidad_catalogo"].strip()
    ]


# --- Escritura en la BD ---------------------------------------------------------------

# tabla -> (columna id, columna de la unidad superior)
_TERRITORIO = {
    "provincia": ("id_provincia", None),
    "distrito": ("id_distrito", "id_provincia"),
    "corregimiento": ("id_corregimiento", "id_distrito"),
}


def _asegurar_unidad(db: Session, tabla: str, unidad: Unidad, id_superior: int | None) -> tuple[int, str]:
    columna_id, columna_superior = _TERRITORIO[tabla]

    existente = db.execute(
        text(f"SELECT {columna_id} FROM {tabla} WHERE codigo = :codigo"), {"codigo": unidad.codigo}
    ).scalar()
    if existente is not None:
        return int(existente), "existente"

    sql = f"SELECT {columna_id}, nombre FROM {tabla} WHERE codigo IS NULL"
    parametros: dict[str, Any] = {}
    if columna_superior:
        sql += f" AND {columna_superior} = :superior"
        parametros["superior"] = id_superior
    for fila in db.execute(text(sql + f" ORDER BY {columna_id}"), parametros):
        if normalizar(fila.nombre) == normalizar(unidad.nombre):
            db.execute(
                text(f"UPDATE {tabla} SET codigo = :codigo, nombre = :nombre WHERE {columna_id} = :id"),
                {"codigo": unidad.codigo, "nombre": unidad.nombre, "id": fila[0]},
            )
            return int(fila[0]), "adoptado"

    columnas = ["codigo", "nombre"] + ([columna_superior] if columna_superior else [])
    valores = {"codigo": unidad.codigo, "nombre": unidad.nombre}
    if columna_superior:
        valores[columna_superior] = id_superior
    nuevo = db.execute(
        text(
            f"INSERT INTO {tabla} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(':' + c for c in columnas)}) RETURNING {columna_id}"
        ),
        valores,
    ).scalar_one()
    return int(nuevo), "creado"


def _sembrar_territorio(db: Session, resumen: dict[str, dict[str, int]]) -> None:
    provincias, distritos, corregimientos = leer_division_politica()
    ids: dict[str, int] = {}
    for tabla, unidades in (("provincia", provincias), ("distrito", distritos), ("corregimiento", corregimientos)):
        conteo = resumen.setdefault(tabla, {"creado": 0, "adoptado": 0, "existente": 0})
        for unidad in unidades:
            id_superior = ids[unidad.codigo_superior] if unidad.codigo_superior else None
            ids[unidad.codigo], accion = _asegurar_unidad(db, tabla, unidad, id_superior)
            conteo[accion] += 1


def _asegurar_por_nombre(db: Session, tabla: str, columna_id: str, nombre: str,
                         extra: dict[str, int] | None = None) -> tuple[int, str]:
    extra = extra or {}
    filtro = "".join(f" AND {c} = :{c}" for c in extra)
    for fila in db.execute(text(f"SELECT {columna_id}, nombre FROM {tabla} WHERE true{filtro} ORDER BY {columna_id}"), extra):
        if normalizar(fila.nombre) == normalizar(nombre):
            return int(fila[0]), "existente"
    columnas = ["nombre", *extra]
    nuevo = db.execute(
        text(
            f"INSERT INTO {tabla} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(':' + c for c in columnas)}) RETURNING {columna_id}"
        ),
        {"nombre": nombre, **extra},
    ).scalar_one()
    return int(nuevo), "creado"


def sembrar(db: Session) -> dict[str, dict[str, int]]:
    """Carga todos los catálogos en la sesión (sin commit) y devuelve cuántos creó o encontró."""
    resumen: dict[str, dict[str, int]] = {}

    def contar(tabla: str, accion: str) -> None:
        conteo = resumen.setdefault(tabla, {"creado": 0, "existente": 0})
        conteo[accion] = conteo.get(accion, 0) + 1

    for nombre in ROLES:
        contar("rol", _asegurar_por_nombre(db, "rol", "id_rol", nombre)[1])

    _sembrar_territorio(db, resumen)

    ids_especialidad: dict[str, int] = {}
    for nombre in leer_especialidades():
        ids_especialidad[normalizar(nombre)], accion = _asegurar_por_nombre(db, "especialidad", "id_especialidad", nombre)
        contar("especialidad", accion)
    for nombre, especialidad in leer_subespecialidades():
        id_especialidad = ids_especialidad[normalizar(especialidad)]
        _, accion = _asegurar_por_nombre(
            db, "subespecialidad", "id_subespecialidad", nombre, {"id_especialidad": id_especialidad}
        )
        contar("subespecialidad", accion)
    return resumen


def main() -> int:
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        print("Cargando catálogos permanentes de SiColMed...")
        resumen = sembrar(db)
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"ERROR: no se pudieron cargar los catálogos: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    for tabla, conteo in resumen.items():
        detalle = ", ".join(f"{accion} {n}" for accion, n in conteo.items() if n)
        print(f"  {tabla}: {detalle}")
    print("Catálogos listos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
