"""Carga datos de prueba (QA) en la base de datos de SiColMed. NUNCA en producción.

Uso (después de `alembic upgrade head` y de `python -m app.scripts.seed_catalogos`):
    docker compose exec api python -m app.scripts.seed_qa

Denegación por defecto: solo corre si ENVIRONMENT es uno de AMBIENTES_QA
(development, qa, test). Sin ENVIRONMENT, con un valor desconocido o con
production, se detiene sin conectarse a la BD.

Crea, a través de las funciones reales de la BD cuando existen (crear_usuario_admin,
crear_cuenta_medico, crear_cuenta, registrar_movimiento, crear_solicitud_cambio,
procesar_solicitud_cambio):
- un administrador y cuatro médicos con certificación vigente, vencida o sin ella,
  de provincias y especialidades distintas;
- cuentas con y sin movimientos (prueban las reglas de eliminar y de cambio de tipo);
- solicitudes de cambio pendiente, aceptada y negada.

Es idempotente: cada registro se busca por una clave estable (número de idoneidad,
correo, nombre de cuenta, descripción del movimiento, marca [QA] del comentario de la
solicitud) y no se vuelve a crear. Nunca borra ni modifica datos existentes.
Qué representa cada registro: docs/datos-prueba.md. Las contraseñas se toman de las
variables DEMO_* y, si no existen, se usan valores de desarrollo; en la BD solo se
guarda su hash.
"""

from __future__ import annotations

import os
import sys


# Únicos ambientes donde se permiten datos QA. Cualquier otro valor se rechaza.
AMBIENTES_QA = frozenset({"development", "qa", "test"})


class AmbienteNoPermitido(RuntimeError):
    """Se intentó cargar datos QA fuera de un ambiente autorizado."""


def verificar_ambiente() -> None:
    valor = os.getenv("ENVIRONMENT")
    ambiente = (valor or "").strip().lower()
    if ambiente in AMBIENTES_QA:
        return
    permitidos = ", ".join(sorted(AMBIENTES_QA))
    if not ambiente:
        motivo = "ENVIRONMENT no está definida"
    elif ambiente == "production":
        motivo = "ENVIRONMENT=production: los datos QA nunca se cargan en producción"
    else:
        motivo = f"ENVIRONMENT={valor!r} no es un ambiente autorizado para datos QA"
    raise AmbienteNoPermitido(
        f"{motivo}. Valores permitidos: {permitidos}. "
        "Los catálogos permanentes se cargan con app.scripts.seed_catalogos en cualquier ambiente."
    )


# Antes de cualquier otro import, para que también se detenga con
# `python app/scripts/seed_qa.py` (sin -m) y sin tocar la BD.
if __name__ == "__main__":
    try:
        verificar_ambiente()
    except AmbienteNoPermitido as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)

from datetime import date  # noqa: E402
from typing import Any  # noqa: E402

from pwdlib import PasswordHash  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.repositories.base import Arg, llamar_escalar  # noqa: E402


def _env(nombre: str, defecto: str) -> str:
    return os.getenv(nombre) or defecto


ADMIN_CORREO = _env("DEMO_ADMIN_EMAIL", "admin@colmed.dev")
ADMIN_PASSWORD = _env("DEMO_ADMIN_PASSWORD", "Admin123!")

# Certificaciones: vigente se calcula también en obtener_perfil_medico a partir de
# fecha_expiracion; aquí se guarda coherente con las fechas.
VIGENTE = {"vigente": True, "fecha_obtencion": date(2025, 1, 15), "puntaje": 95, "fecha_expiracion": date(2030, 1, 15)}
VENCIDA = {"vigente": False, "fecha_obtencion": date(2019, 1, 10), "puntaje": 80, "fecha_expiracion": date(2024, 1, 10)}

# corregimiento: código oficial DPA 2025 (lo cargó seed_catalogos)
MEDICOS: tuple[dict[str, Any], ...] = (
    {
        "numero_idoneidad": "IDONEIDAD-0001", "numero_registro_medico": "RM-0001", "cedula": "8-111-111",
        "primer_nombre": "Ana", "segundo_nombre": "Maria", "apellido_paterno": "Perez", "apellido_materno": "Gomez",
        "fecha_nacimiento": date(1985, 3, 14), "telefono_residencial": "507-111-1111", "celular": "507-611-1111",
        "email_personal": "ana.perez@example.com",
        "correo": _env("DEMO_MEDICO1_EMAIL", "medico1@colmed.dev"), "password": _env("DEMO_MEDICO1_PASSWORD", "Medico123!"),
        "corregimiento": "080807",  # Bella Vista, Panamá, Panamá
        "especialidad": "Medicina interna", "subespecialidad": "Cardiología",
        "certificacion": VIGENTE, "escenario": "Certificación vigente",
    },
    {
        "numero_idoneidad": "IDONEIDAD-0002", "numero_registro_medico": "RM-0002", "cedula": "8-222-222",
        "primer_nombre": "Luis", "segundo_nombre": None, "apellido_paterno": "Rodriguez", "apellido_materno": "Diaz",
        "fecha_nacimiento": date(1979, 11, 2), "telefono_residencial": "507-222-2222", "celular": "507-622-2222",
        "email_personal": "luis.rodriguez@example.com",
        "correo": _env("DEMO_MEDICO2_EMAIL", "medico2@colmed.dev"), "password": _env("DEMO_MEDICO2_PASSWORD", "Medico123!"),
        "corregimiento": "080807",
        "especialidad": "Pediatría", "subespecialidad": None,
        "certificacion": VENCIDA, "escenario": "Certificación vencida",
    },
    {
        "numero_idoneidad": "IDONEIDAD-0003", "numero_registro_medico": "RM-0003", "cedula": "4-333-333",
        "primer_nombre": "Carmen", "segundo_nombre": "Isabel", "apellido_paterno": "Sanchez", "apellido_materno": "Rios",
        "fecha_nacimiento": date(1990, 6, 21), "telefono_residencial": "507-333-3333", "celular": "507-633-3333",
        "email_personal": "carmen.sanchez@example.com",
        "correo": _env("DEMO_MEDICO3_EMAIL", "medico3@colmed.dev"), "password": _env("DEMO_MEDICO3_PASSWORD", "Medico123!"),
        "corregimiento": "040601",  # David, David, Chiriquí
        "especialidad": "Ginecología y obstetricia", "subespecialidad": None,
        "certificacion": None, "escenario": "Sin certificación registrada",
    },
    {
        "numero_idoneidad": "IDONEIDAD-0004", "numero_registro_medico": "RM-0004", "cedula": "9-444-444",
        "primer_nombre": "Jorge", "segundo_nombre": None, "apellido_paterno": "Castillo", "apellido_materno": "Vega",
        "fecha_nacimiento": date(1982, 9, 5), "telefono_residencial": "507-444-4444", "celular": "507-644-4444",
        "email_personal": "jorge.castillo@example.com",
        "correo": _env("DEMO_MEDICO4_EMAIL", "medico4@colmed.dev"), "password": _env("DEMO_MEDICO4_PASSWORD", "Medico123!"),
        "corregimiento": "091001",  # Santiago, Santiago, Veraguas
        "especialidad": "Cirugía general", "subespecialidad": None,
        "certificacion": VIGENTE, "escenario": "Certificación vigente (otra provincia)",
    },
)

# nombre -> (tipo, escenario). Los movimientos de MOVIMIENTOS las dejan con o sin movimientos.
CUENTAS: dict[str, tuple[str, str]] = {
    "QA Caja general": ("DEBITO", "Con movimientos: eliminar la desactiva y no se puede cambiar el tipo"),
    "QA Banco operativo": ("DEBITO", "Con movimientos"),
    "QA Ingresos por cuotas": ("CREDITO", "Con movimientos"),
    "QA Cuenta sin movimientos": ("DEBITO", "Sin movimientos: se puede eliminar y cambiar de tipo"),
}

MOVIMIENTOS: tuple[dict[str, Any], ...] = (
    {
        "descripcion": "QA - Cobro de cuotas de enero", "fecha": date(2026, 1, 15),
        "detalle": (("QA Caja general", "150.00", "DEBITO"), ("QA Ingresos por cuotas", "150.00", "CREDITO")),
    },
    {
        "descripcion": "QA - Depósito de caja en banco", "fecha": date(2026, 1, 20),
        "detalle": (("QA Banco operativo", "100.00", "DEBITO"), ("QA Caja general", "100.00", "CREDITO")),
    },
)

# Estados reales: solicitud_cambio.estado es PENDIENTE o PROCESADO, y cada campo
# guarda APROBADO/RECHAZADO (procesar_solicitud_cambio). "Aceptada" y "Negada" son
# solicitudes PROCESADO con todos sus campos APROBADO o RECHAZADO.
SOLICITUDES: tuple[dict[str, Any], ...] = (
    {"marca": "[QA] Solicitud pendiente", "medico": "IDONEIDAD-0001", "puntaje": 97, "decision": None},
    {"marca": "[QA] Solicitud aceptada", "medico": "IDONEIDAD-0004", "puntaje": 98, "decision": "APROBADO"},
    {"marca": "[QA] Solicitud negada", "medico": "IDONEIDAD-0002", "puntaje": 99, "decision": "RECHAZADO"},
)


def _uno(db: Session, sql: str, **parametros: Any) -> Any:
    return db.execute(text(sql), parametros).scalar()


def _id_por_codigo(db: Session, codigo: str) -> tuple[int, int, int]:
    fila = db.execute(
        text(
            "SELECT d.id_provincia, c.id_distrito, c.id_corregimiento "
            "FROM corregimiento c JOIN distrito d ON d.id_distrito = c.id_distrito "
            "WHERE c.codigo = :codigo"
        ),
        {"codigo": codigo},
    ).first()
    if fila is None:
        raise RuntimeError(
            f"No existe el corregimiento {codigo}: ejecuta primero python -m app.scripts.seed_catalogos"
        )
    return int(fila[0]), int(fila[1]), int(fila[2])


def _id_catalogo(db: Session, tabla: str, nombre: str) -> int:
    valor = _uno(db, f"SELECT id_{tabla} FROM {tabla} WHERE nombre = :nombre ORDER BY id_{tabla} LIMIT 1", nombre=nombre)
    if valor is None:
        raise RuntimeError(f"No existe {tabla} {nombre!r}: ejecuta primero python -m app.scripts.seed_catalogos")
    return int(valor)


def _sembrar_admin(db: Session, hasher: PasswordHash) -> int:
    existente = _uno(db, "SELECT id_usuario FROM usuario WHERE lower(correo) = lower(:correo)", correo=ADMIN_CORREO)
    if existente is not None:
        print(f"  admin {ADMIN_CORREO}: existente (id {existente})")
        return int(existente)

    admin_activo = _uno(
        db,
        "SELECT u.id_usuario FROM usuario u JOIN rol r ON r.id_rol = u.id_rol "
        "WHERE lower(btrim(r.nombre)) = 'admin_cmp' AND u.activo ORDER BY u.id_usuario LIMIT 1",
    )
    id_usuario = llamar_escalar(db, "crear_usuario_admin", {
        "p_correo": ADMIN_CORREO,
        "p_password_hash": hasher.hash(ADMIN_PASSWORD),
        "p_id_administrador": Arg(admin_activo, "integer"),
    })
    print(f"  admin {ADMIN_CORREO}: creado (id {id_usuario})")
    return int(id_usuario)


def _sembrar_medico(db: Session, hasher: PasswordHash, datos: dict[str, Any]) -> int:
    id_medico = _uno(db, "SELECT id_medico FROM medico WHERE numero_idoneidad = :n", n=datos["numero_idoneidad"])
    creado = id_medico is None
    if creado:
        id_provincia, id_distrito, id_corregimiento = _id_por_codigo(db, datos["corregimiento"])
        id_direccion = db.execute(
            text(
                "INSERT INTO direccion (apartado_postal, calle, edificio, numero_direccion, "
                "id_provincia, id_distrito, id_corregimiento) "
                "VALUES ('0801', 'Calle QA', 'Edificio QA', '100', :p, :d, :c) RETURNING id_direccion"
            ),
            {"p": id_provincia, "d": id_distrito, "c": id_corregimiento},
        ).scalar_one()
        campos = ("numero_idoneidad", "numero_registro_medico", "cedula", "primer_nombre", "segundo_nombre",
                  "apellido_paterno", "apellido_materno", "fecha_nacimiento", "telefono_residencial",
                  "celular", "email_personal")
        id_medico = db.execute(
            text(
                f"INSERT INTO medico ({', '.join(campos)}, id_direccion) "
                f"VALUES ({', '.join(':' + c for c in campos)}, :id_direccion) RETURNING id_medico"
            ),
            {**{c: datos[c] for c in campos}, "id_direccion": id_direccion},
        ).scalar_one()
    id_medico = int(id_medico)

    # Relaciones: solo se agregan si faltan (un médico que ya existía conserva las suyas)
    relaciones = [("medico_especialidad", "id_especialidad", _id_catalogo(db, "especialidad", datos["especialidad"]))]
    if datos["subespecialidad"]:
        relaciones.append(("medico_subespecialidad", "id_subespecialidad",
                           _id_catalogo(db, "subespecialidad", datos["subespecialidad"])))
    for tabla, columna, valor in relaciones:
        db.execute(
            text(
                f"INSERT INTO {tabla} (id_medico, {columna}) SELECT :m, :v "
                f"WHERE NOT EXISTS (SELECT 1 FROM {tabla} WHERE id_medico = :m AND {columna} = :v)"
            ),
            {"m": id_medico, "v": valor},
        )

    # Certificación: solo si el médico no tiene ninguna
    if datos["certificacion"] and _uno(db, "SELECT count(*) FROM certificacion WHERE id_medico = :m", m=id_medico) == 0:
        db.execute(
            text(
                "INSERT INTO certificacion (id_medico, vigente, fecha_obtencion, puntaje, fecha_expiracion) "
                "VALUES (:m, :vigente, :fecha_obtencion, :puntaje, :fecha_expiracion)"
            ),
            {"m": id_medico, **datos["certificacion"]},
        )

    # Cuenta de acceso
    tiene_usuario = _uno(db, "SELECT id_usuario FROM medico WHERE id_medico = :m", m=id_medico) is not None
    correo_usado = _uno(db, "SELECT id_usuario FROM usuario WHERE lower(correo) = lower(:c)", c=datos["correo"])
    if not tiene_usuario and correo_usado is None:
        llamar_escalar(db, "crear_cuenta_medico", {
            "p_numero_idoneidad": datos["numero_idoneidad"],
            "p_correo": datos["correo"],
            "p_password_hash": hasher.hash(datos["password"]),
        })
    print(f"  medico {datos['numero_idoneidad']}: {'creado' if creado else 'existente'} (id {id_medico}) "
          f"- {datos['escenario']}")
    return id_medico


def _sembrar_cuentas(db: Session) -> dict[str, int]:
    ids: dict[str, int] = {}
    for nombre, (tipo, _) in CUENTAS.items():
        existente = _uno(db, "SELECT id_cuenta FROM cuenta WHERE nombre = :n", n=nombre)
        ids[nombre] = int(existente) if existente is not None else int(
            llamar_escalar(db, "crear_cuenta", {"nombre": Arg(nombre, "text"), "tipo": Arg(tipo, "text")})
        )
        print(f"  cuenta {nombre!r}: {'existente' if existente else 'creada'} (id {ids[nombre]})")

    for movimiento in MOVIMIENTOS:
        existente = _uno(db, "SELECT id_movimiento FROM movimiento WHERE descripcion = :d", d=movimiento["descripcion"])
        if existente is None:
            detalle = [{"id_cuenta": ids[c], "monto": monto, "tipo": tipo} for c, monto, tipo in movimiento["detalle"]]
            existente = llamar_escalar(db, "registrar_movimiento", {
                "fecha": Arg(movimiento["fecha"], "date"),
                "descripcion": Arg(movimiento["descripcion"], "text"),
                "detalle": Arg(detalle, "jsonb"),
            })
        print(f"  movimiento {movimiento['descripcion']!r}: id {existente}")
    return ids


def _sembrar_solicitudes(db: Session, id_admin: int, ids_medico: dict[str, int]) -> None:
    for solicitud in SOLICITUDES:
        existente = _uno(db, "SELECT id_solicitud_cambio FROM solicitud_cambio WHERE comentario = :c", c=solicitud["marca"])
        if existente is None:
            id_medico = ids_medico[solicitud["medico"]]
            id_certificacion = _uno(
                db, "SELECT id_certificacion FROM certificacion WHERE id_medico = :m ORDER BY id_certificacion LIMIT 1",
                m=id_medico,
            )
            existente = llamar_escalar(db, "crear_solicitud_cambio", {
                "id_medico": Arg(id_medico, "integer"),
                "cambios": Arg({"certificaciones": [{"id_certificacion": id_certificacion,
                                                    "puntaje": solicitud["puntaje"]}]}, "jsonb"),
            })
            if solicitud["decision"] is None:
                # crear_solicitud_cambio no recibe comentario; la marca permite encontrarla otra vez
                db.execute(text("UPDATE solicitud_cambio SET comentario = :c WHERE id_solicitud_cambio = :id"),
                           {"c": solicitud["marca"], "id": existente})
            else:
                llamar_escalar(db, "procesar_solicitud_cambio", {
                    "id_solicitud_cambio": Arg(existente, "integer"),
                    "id_administrador": Arg(id_admin, "integer"),
                    "decisiones": Arg({"certificaciones": [{"puntaje": solicitud["decision"]}]}, "jsonb"),
                    "comentario": Arg(solicitud["marca"], "text"),
                })
        estado = _uno(db, "SELECT estado FROM solicitud_cambio WHERE id_solicitud_cambio = :id", id=existente)
        print(f"  solicitud {solicitud['marca']!r}: id {existente}, estado {estado}")


def sembrar(db: Session) -> None:
    """Carga los datos QA en la sesión (sin commit). Falla en producción."""
    verificar_ambiente()
    hasher = PasswordHash.recommended()
    id_admin = _sembrar_admin(db, hasher)
    ids_medico = {m["numero_idoneidad"]: _sembrar_medico(db, hasher, m) for m in MEDICOS}
    _sembrar_cuentas(db)
    _sembrar_solicitudes(db, id_admin, ids_medico)


def main() -> int:
    try:
        verificar_ambiente()
    except AmbienteNoPermitido as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        print("Cargando datos de prueba QA de SiColMed...")
        sembrar(db)
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"ERROR: no se pudieron cargar los datos QA: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print("Datos QA listos (contraseñas de prueba en docs/datos-prueba.md):")
    print(f"  admin:   {ADMIN_CORREO}")
    for datos in MEDICOS:
        print(f"  medico:  {datos['correo']} ({datos['escenario']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
