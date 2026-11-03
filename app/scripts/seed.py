"""Carga datos de demostracion en la base de datos de SiColMed.

Uso:
    docker compose exec api python -m app.scripts.seed

El script es idempotente: se puede ejecutar varias veces sin duplicar datos y
nunca borra ni modifica registros existentes. Las contrasenas se toman de las
variables de entorno DEMO_* y, si no existen, se usan valores de desarrollo.
"""

from __future__ import annotations

import os
import sys
from datetime import date
from typing import Any

from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repositories.base import Arg, llamar_escalar

ROLES = ("admin_cmp", "medico", "tesorero", "admin_asociacion")

PROVINCIA = "Panama"
DISTRITO = "Panama"
CORREGIMIENTO = "Bella Vista"
ESPECIALIDAD = "Medicina General"


def _env(nombre: str, defecto: str) -> str:
    return os.getenv(nombre) or defecto


ADMIN_CORREO = _env("DEMO_ADMIN_EMAIL", "admin@colmed.dev")
ADMIN_PASSWORD = _env("DEMO_ADMIN_PASSWORD", "Admin123!")

MEDICOS: tuple[dict[str, Any], ...] = (
    {
        "numero_idoneidad": "IDONEIDAD-0001",
        "numero_registro_medico": "RM-0001",
        "cedula": "8-111-111",
        "primer_nombre": "Ana",
        "segundo_nombre": "Maria",
        "apellido_paterno": "Perez",
        "apellido_materno": "Gomez",
        "fecha_nacimiento": date(1985, 3, 14),
        "telefono_residencial": "507-111-1111",
        "celular": "507-611-1111",
        "email_personal": "ana.perez@example.com",
        "correo": _env("DEMO_MEDICO1_EMAIL", "medico1@colmed.dev"),
        "password": _env("DEMO_MEDICO1_PASSWORD", "Medico123!"),
    },
    {
        "numero_idoneidad": "IDONEIDAD-0002",
        "numero_registro_medico": "RM-0002",
        "cedula": "8-222-222",
        "primer_nombre": "Luis",
        "segundo_nombre": None,
        "apellido_paterno": "Rodriguez",
        "apellido_materno": "Diaz",
        "fecha_nacimiento": date(1979, 11, 2),
        "telefono_residencial": "507-222-2222",
        "celular": "507-622-2222",
        "email_personal": "luis.rodriguez@example.com",
        "correo": _env("DEMO_MEDICO2_EMAIL", "medico2@colmed.dev"),
        "password": _env("DEMO_MEDICO2_PASSWORD", "Medico123!"),
    },
)

_CATALOGOS: dict[str, dict[str, Any]] = {
    "provincia": {"id": "id_provincia", "filtros": ()},
    "distrito": {"id": "id_distrito", "filtros": ("id_provincia",)},
    "corregimiento": {"id": "id_corregimiento", "filtros": ("id_distrito",)},
    "especialidad": {"id": "id_especialidad", "filtros": ()},
}


def _asegurar_rol(db: Session, nombre: str) -> tuple[int, bool]:
    existente = db.execute(
        text(
            "SELECT id_rol FROM rol "
            "WHERE lower(btrim(nombre)) = lower(btrim(:nombre)) "
            "ORDER BY id_rol LIMIT 1"
        ),
        {"nombre": nombre},
    ).scalar()
    if existente is not None:
        return int(existente), False

    nuevo = db.execute(
        text("INSERT INTO rol (nombre) VALUES (:nombre) RETURNING id_rol"),
        {"nombre": nombre},
    ).scalar_one()
    return int(nuevo), True


def _asegurar_catalogo(
    db: Session,
    tabla: str,
    nombre: str,
    filtros: dict[str, int] | None = None,
) -> tuple[int, bool]:
    config = _CATALOGOS.get(tabla)
    if config is None:
        raise ValueError(f"Tabla de catalogo no permitida: {tabla!r}")

    filtros = filtros or {}
    desconocidos = set(filtros) - set(config["filtros"])
    if desconocidos:
        raise ValueError(f"Filtros no permitidos para {tabla}: {desconocidos}")

    columna_id = config["id"]
    sql = (
        f"SELECT {columna_id} FROM {tabla} "
        "WHERE lower(btrim(nombre)) = lower(btrim(:nombre))"
    )
    parametros: dict[str, Any] = {"nombre": nombre}
    for columna, valor in filtros.items():
        sql += f" AND {columna} = :{columna}"
        parametros[columna] = valor
    sql += f" ORDER BY {columna_id} LIMIT 1"

    existente = db.execute(text(sql), parametros).scalar()
    if existente is not None:
        return int(existente), False

    columnas = ["nombre", *filtros.keys()]
    valores = [":nombre", *(f":{c}" for c in filtros)]
    nuevo = db.execute(
        text(
            f"INSERT INTO {tabla} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(valores)}) "
            f"RETURNING {columna_id}"
        ),
        parametros,
    ).scalar_one()
    return int(nuevo), True


def _asegurar_geografia(db: Session) -> tuple[int, int, int]:
    id_provincia, _ = _asegurar_catalogo(db, "provincia", PROVINCIA)
    id_distrito, _ = _asegurar_catalogo(
        db, "distrito", DISTRITO, {"id_provincia": id_provincia}
    )
    id_corregimiento, _ = _asegurar_catalogo(
        db, "corregimiento", CORREGIMIENTO, {"id_distrito": id_distrito}
    )
    return id_provincia, id_distrito, id_corregimiento


def _crear_direccion(
    db: Session, id_provincia: int, id_distrito: int, id_corregimiento: int
) -> int:
    id_direccion = db.execute(
        text(
            "INSERT INTO direccion ("
            "apartado_postal, calle, edificio, numero_direccion, "
            "id_provincia, id_distrito, id_corregimiento"
            ") VALUES ("
            ":apartado_postal, :calle, :edificio, :numero_direccion, "
            ":id_provincia, :id_distrito, :id_corregimiento"
            ") RETURNING id_direccion"
        ),
        {
            "apartado_postal": "0801",
            "calle": "Calle Demo",
            "edificio": "Edificio Demo",
            "numero_direccion": "100",
            "id_provincia": id_provincia,
            "id_distrito": id_distrito,
            "id_corregimiento": id_corregimiento,
        },
    ).scalar_one()
    return int(id_direccion)


def _sembrar_admin(db: Session, hasher: PasswordHash) -> tuple[int, bool]:
    existente = db.execute(
        text("SELECT id_usuario FROM usuario WHERE lower(correo) = lower(:correo)"),
        {"correo": ADMIN_CORREO},
    ).scalar()
    if existente is not None:
        print(f"  admin {ADMIN_CORREO}: existente (id {existente})")
        return int(existente), False

    admin_activo = db.execute(
        text(
            "SELECT u.id_usuario "
            "FROM usuario u JOIN rol r ON r.id_rol = u.id_rol "
            "WHERE lower(btrim(r.nombre)) = 'admin_cmp' AND u.activo "
            "ORDER BY u.id_usuario LIMIT 1"
        )
    ).scalar()

    parametros: dict[str, Any] = {
        "p_correo": ADMIN_CORREO,
        "p_password_hash": hasher.hash(ADMIN_PASSWORD),
        "p_id_administrador": Arg(
            admin_activo if admin_activo is not None else None, "integer"
        ),
    }
    id_usuario = llamar_escalar(db, "crear_usuario_admin", parametros)
    print(f"  admin {ADMIN_CORREO}: creado (id {id_usuario})")
    return int(id_usuario), True


def _sembrar_medico(
    db: Session,
    hasher: PasswordHash,
    datos: dict[str, Any],
    ids_geo: tuple[int, int, int],
    id_especialidad: int,
) -> tuple[int, int, bool, bool]:
    fila = db.execute(
        text(
            "SELECT id_medico, id_usuario FROM medico "
            "WHERE numero_idoneidad = :numero_idoneidad"
        ),
        {"numero_idoneidad": datos["numero_idoneidad"]},
    ).first()

    if fila is not None:
        id_medico = int(fila.id_medico)
        id_usuario = int(fila.id_usuario) if fila.id_usuario is not None else None
        medico_creado = False
    else:
        id_provincia, id_distrito, id_corregimiento = ids_geo
        id_direccion = _crear_direccion(
            db, id_provincia, id_distrito, id_corregimiento
        )
        id_medico = int(
            db.execute(
                text(
                    "INSERT INTO medico ("
                    "numero_idoneidad, numero_registro_medico, cedula, "
                    "primer_nombre, segundo_nombre, apellido_paterno, "
                    "apellido_materno, fecha_nacimiento, telefono_residencial, "
                    "celular, email_personal, id_direccion"
                    ") VALUES ("
                    ":numero_idoneidad, :numero_registro_medico, :cedula, "
                    ":primer_nombre, :segundo_nombre, :apellido_paterno, "
                    ":apellido_materno, :fecha_nacimiento, :telefono_residencial, "
                    ":celular, :email_personal, :id_direccion"
                    ") RETURNING id_medico"
                ),
                {
                    "numero_idoneidad": datos["numero_idoneidad"],
                    "numero_registro_medico": datos["numero_registro_medico"],
                    "cedula": datos["cedula"],
                    "primer_nombre": datos["primer_nombre"],
                    "segundo_nombre": datos["segundo_nombre"],
                    "apellido_paterno": datos["apellido_paterno"],
                    "apellido_materno": datos["apellido_materno"],
                    "fecha_nacimiento": datos["fecha_nacimiento"],
                    "telefono_residencial": datos["telefono_residencial"],
                    "celular": datos["celular"],
                    "email_personal": datos["email_personal"],
                    "id_direccion": id_direccion,
                },
            ).scalar_one()
        )
        id_usuario = None
        medico_creado = True

    db.execute(
        text(
            "INSERT INTO medico_especialidad (id_medico, id_especialidad) "
            "SELECT :id_medico, :id_especialidad "
            "WHERE NOT EXISTS ("
            "SELECT 1 FROM medico_especialidad "
            "WHERE id_medico = :id_medico AND id_especialidad = :id_especialidad"
            ")"
        ),
        {"id_medico": id_medico, "id_especialidad": id_especialidad},
    )

    cuenta_creada = False
    if id_usuario is None:
        correo_existente = db.execute(
            text("SELECT id_usuario FROM usuario WHERE lower(correo) = lower(:correo)"),
            {"correo": datos["correo"]},
        ).scalar()
        if correo_existente is not None:
            print(
                f"  medico {datos['numero_idoneidad']}: "
                f"cuenta {datos['correo']} ya existe (id {correo_existente})"
            )
            id_usuario = int(correo_existente)
        else:
            id_usuario = int(
                llamar_escalar(
                    db,
                    "crear_cuenta_medico",
                    {
                        "p_numero_idoneidad": datos["numero_idoneidad"],
                        "p_correo": datos["correo"],
                        "p_password_hash": hasher.hash(datos["password"]),
                    },
                )
            )
            cuenta_creada = True

    print(
        f"  medico {datos['numero_idoneidad']}: "
        f"{'creado' if medico_creado else 'existente'} (id {id_medico}), "
        f"cuenta {'creada' if cuenta_creada else 'existente'} "
        f"(id {id_usuario})"
    )
    return id_medico, int(id_usuario), medico_creado, cuenta_creada


def main() -> int:
    hasher = PasswordHash.recommended()
    db = SessionLocal()
    try:
        print("Sembrando datos de demostracion de SiColMed...")

        for nombre in ROLES:
            id_rol, creado = _asegurar_rol(db, nombre)
            print(f"  rol {nombre}: {'creado' if creado else 'existente'} (id {id_rol})")

        id_provincia, id_distrito, id_corregimiento = _asegurar_geografia(db)
        id_especialidad, _ = _asegurar_catalogo(
            db, "especialidad", ESPECIALIDAD
        )
        print(
            "  catalogos: "
            f"provincia={id_provincia}, distrito={id_distrito}, "
            f"corregimiento={id_corregimiento}, especialidad={id_especialidad}"
        )

        _sembrar_admin(db, hasher)

        ids_geo = (id_provincia, id_distrito, id_corregimiento)
        for datos in MEDICOS:
            _sembrar_medico(db, hasher, datos, ids_geo, id_especialidad)

        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"ERROR: no se pudo sembrar la base de datos: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print("Datos de demostracion listos.")
    print(f"  admin:   {ADMIN_CORREO} / {ADMIN_PASSWORD}")
    for datos in MEDICOS:
        print(f"  medico:  {datos['correo']} / {datos['password']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
