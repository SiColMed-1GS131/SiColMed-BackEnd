"""Pruebas de integración de seed_catalogos y seed_qa contra PostgreSQL real.

Se saltan si no se define SICOLMED_TEST_DATABASE_URL: una BD con `alembic upgrade head`
aplicado y que se pueda usar para pruebas. Todo corre en una transacción que se deshace
al final, así que no deja cambios.

    docker compose exec -e SICOLMED_TEST_DATABASE_URL=postgresql+psycopg://.../sicolmed_prueba \
        api pytest app/tests/test_seeds_postgres.py
"""
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.repositories.base import Arg, llamar_escalar
from app.scripts import seed_catalogos, seed_qa

URL = os.getenv("SICOLMED_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="Define SICOLMED_TEST_DATABASE_URL para usar PostgreSQL")

TABLAS = ("rol", "provincia", "distrito", "corregimiento", "especialidad", "subespecialidad",
          "usuario", "medico", "direccion", "certificacion", "medico_especialidad",
          "medico_subespecialidad", "cuenta", "movimiento", "movimiento_cuenta", "solicitud_cambio")


@pytest.fixture
def db(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    motor = create_engine(URL)
    conexion = motor.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
    yield sesion
    sesion.close()
    transaccion.rollback()
    conexion.close()
    motor.dispose()


def _conteos(db):
    return {t: db.execute(text(f"SELECT count(*) FROM {t}")).scalar() for t in TABLAS}


def _foto(db):
    """Contenido completo de cada fila (identidad y valores), ordenado por su clave primaria."""
    return {
        t: db.execute(text(f"SELECT to_jsonb(x)::text FROM {t} x ORDER BY 1")).scalars().all()
        for t in TABLAS
    }


def _uno(db, sql, **p):
    return db.execute(text(sql), p).scalar()


def test_seeds_idempotentes_y_escenarios(db):
    seed_catalogos.sembrar(db)
    seed_qa.sembrar(db)
    db.flush()
    antes = _conteos(db)
    foto = _foto(db)
    seed_catalogos.sembrar(db)
    seed_qa.sembrar(db)
    db.flush()
    assert _conteos(db) == antes
    # No solo los conteos: mismas filas, mismos id y mismos valores en todas las tablas
    despues = _foto(db)
    for tabla in TABLAS:
        assert despues[tabla] == foto[tabla], f"{tabla} cambió en la segunda ejecución"

    # Catálogos completos y sin códigos repetidos
    assert _uno(db, "SELECT count(DISTINCT codigo) FROM provincia WHERE codigo IS NOT NULL") == 13
    assert _uno(db, "SELECT count(DISTINCT codigo) FROM distrito WHERE codigo IS NOT NULL") == 83
    assert _uno(db, "SELECT count(DISTINCT codigo) FROM corregimiento WHERE codigo IS NOT NULL") == 698
    assert _uno(db, "SELECT count(*) FROM corregimiento WHERE codigo = '010501'") == 0
    # Relaciones: cada corregimiento con su distrito según el código oficial
    assert _uno(db, """SELECT count(*) FROM corregimiento c JOIN distrito d USING (id_distrito)
                       WHERE c.codigo IS NOT NULL AND left(c.codigo, 4) <> d.codigo""") == 0
    assert _uno(db, """SELECT count(*) FROM distrito d JOIN provincia p USING (id_provincia)
                       WHERE d.codigo IS NOT NULL AND left(d.codigo, 2) <> p.codigo""") == 0

    # Médicos: certificación vigente, vencida y ninguna; direcciones coherentes
    vigencia = dict(db.execute(text(
        """SELECT m.numero_idoneidad, bool_or(c.fecha_expiracion >= CURRENT_DATE)
             FROM medico m LEFT JOIN certificacion c USING (id_medico)
            WHERE m.numero_idoneidad LIKE 'IDONEIDAD-000%' GROUP BY 1""")).all())
    assert vigencia["IDONEIDAD-0001"] is True
    assert vigencia["IDONEIDAD-0002"] is False
    assert vigencia["IDONEIDAD-0003"] is None
    assert _uno(db, """SELECT count(*) FROM medico m JOIN direccion x USING (id_direccion)
                       JOIN corregimiento c ON c.id_corregimiento = x.id_corregimiento
                       JOIN distrito d ON d.id_distrito = x.id_distrito
                      WHERE c.id_distrito <> x.id_distrito OR d.id_provincia <> x.id_provincia""") == 0
    assert _uno(db, """SELECT count(*) FROM medico m JOIN usuario u USING (id_usuario)
                      WHERE m.numero_idoneidad LIKE 'IDONEIDAD-000%'
                        AND u.password_hash NOT LIKE '$%'""") == 0

    # Solicitudes en los tres estados
    estados = dict(db.execute(text(
        "SELECT comentario, estado FROM solicitud_cambio WHERE comentario LIKE '[QA]%'")).all())
    assert estados == {"[QA] Solicitud pendiente": "PENDIENTE",
                       "[QA] Solicitud aceptada": "PROCESADO",
                       "[QA] Solicitud negada": "PROCESADO"}


def test_restricciones_de_cuentas(db):
    seed_catalogos.sembrar(db)
    seed_qa.sembrar(db)
    con = _uno(db, "SELECT id_cuenta FROM cuenta WHERE nombre = 'QA Caja general'")
    sin = _uno(db, "SELECT id_cuenta FROM cuenta WHERE nombre = 'QA Cuenta sin movimientos'")

    # Directo y en un savepoint: llamar_escalar hace rollback de toda la sesión al fallar
    with pytest.raises(DBAPIError, match="ya tiene movimientos"):
        with db.begin_nested():
            db.execute(text("SELECT editar_cuenta(:i, NULL, 'CREDITO', NULL)"), {"i": con})
    assert llamar_escalar(db, "eliminar_cuenta", {"id": Arg(con, "integer")}) == "DESACTIVADA"

    llamar_escalar(db, "editar_cuenta", {"id": Arg(sin, "integer"), "nombre": Arg(None, "text"),
                                         "tipo": Arg("CREDITO", "text"), "activa": Arg(None, "boolean")})
    assert _uno(db, "SELECT tipo FROM cuenta WHERE id_cuenta = :i", i=sin) == "CREDITO"
    assert llamar_escalar(db, "eliminar_cuenta", {"id": Arg(sin, "integer")}) == "ELIMINADA"


def test_segunda_ejecucion_no_sobrescribe_datos_legitimos(db):
    """Cambios hechos por usuarios después del seed deben sobrevivir a otra ejecución."""
    seed_catalogos.sembrar(db)
    seed_qa.sembrar(db)
    cambios = {
        # nombre de una unidad con código oficial (p. ej. corregido por Base de Datos)
        "UPDATE corregimiento SET nombre = 'David (cabecera)' WHERE codigo = '040601'": (
            "SELECT nombre FROM corregimiento WHERE codigo = '040601'", "David (cabecera)"),
        # datos de contacto que el médico actualizó
        "UPDATE medico SET celular = '507-699-0000' WHERE numero_idoneidad = 'IDONEIDAD-0003'": (
            "SELECT celular FROM medico WHERE numero_idoneidad = 'IDONEIDAD-0003'", "507-699-0000"),
        # puntaje corregido de una certificación
        "UPDATE certificacion SET puntaje = 70 WHERE id_medico = "
        "(SELECT id_medico FROM medico WHERE numero_idoneidad = 'IDONEIDAD-0002')": (
            "SELECT puntaje FROM certificacion c JOIN medico m USING (id_medico) "
            "WHERE m.numero_idoneidad = 'IDONEIDAD-0002'", 70),
        # cuenta desactivada por tesorería
        "UPDATE cuenta SET activa = false WHERE nombre = 'QA Banco operativo'": (
            "SELECT activa FROM cuenta WHERE nombre = 'QA Banco operativo'", False),
        # contraseña cambiada por el usuario
        "UPDATE usuario SET password_hash = '$argon2id$cambiada' WHERE correo = 'medico1@colmed.dev'": (
            "SELECT password_hash FROM usuario WHERE correo = 'medico1@colmed.dev'", "$argon2id$cambiada"),
    }
    for sql in cambios:
        db.execute(text(sql))
    antes = _conteos(db)

    seed_catalogos.sembrar(db)
    seed_qa.sembrar(db)
    db.flush()

    for consulta, esperado in cambios.values():
        assert _uno(db, consulta) == esperado, consulta
    assert _conteos(db) == antes


@pytest.mark.xfail(strict=True, reason=(
    "Defecto conocido: especialidad y subespecialidad no tienen clave estable (no hay código "
    "oficial) y el seed las busca por nombre; si se renombra una, la vuelve a crear. "
    "Requiere decisión de Base de Datos (docs/fuentes-especialidades.md)."))
def test_especialidad_renombrada_no_se_duplica(db):
    seed_catalogos.sembrar(db)
    seed_qa.sembrar(db)
    db.execute(text("UPDATE especialidad SET nombre = 'Pediatría general' WHERE nombre = 'Pediatría'"))
    antes = _conteos(db)
    seed_catalogos.sembrar(db)
    seed_qa.sembrar(db)
    db.flush()
    assert _conteos(db) == antes


def test_adopcion_de_filas_sin_codigo_ocurre_una_sola_vez(db):
    """Una fila antigua sin código se adopta (código + nombre oficial) y después no se toca."""
    seed_catalogos.sembrar(db)
    id_bocas = _uno(db, "SELECT id_provincia FROM provincia WHERE codigo = '01'")
    # Simula una fila del seed antiguo: sin código y sin tilde
    db.execute(text("UPDATE provincia SET codigo = NULL, nombre = 'Bocas del toro' WHERE id_provincia = :i"),
               {"i": id_bocas})
    seed_catalogos.sembrar(db)
    fila = db.execute(text("SELECT codigo, nombre FROM provincia WHERE id_provincia = :i"), {"i": id_bocas}).one()
    assert tuple(fila) == ("01", "Bocas del Toro")
    assert _uno(db, "SELECT count(*) FROM provincia WHERE codigo = '01'") == 1
