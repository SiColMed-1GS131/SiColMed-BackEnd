"""agrega funciones de intentos de inicio de sesion

FIX DE EMERGENCIA, revisar por BD. Hecho por Desarrollo (no por Base de Datos)
para corregir DEF-006: el login no bloqueaba la cuenta tras 5 intentos fallidos
y log_inicio_sesion quedaba vacia. Agrega dos funciones sobre la tabla existente
log_inicio_sesion (no cambia tablas):
- registrar_intento_inicio_sesion(p_id_usuario, p_exitoso): inserta el intento
  con resultado 'EXITOSO' o 'FALLIDO' y fecha = localtimestamp.
- listar_intentos_inicio_sesion(p_id_usuario, p_limite): ultimos intentos, del
  mas reciente al mas antiguo, con los segundos transcurridos segun la BD.
Base de Datos debe revisar y confirmar estas definiciones.
Fuente: app/funciones/registrar_intento_inicio_sesion.sql y
app/funciones/listar_intentos_inicio_sesion.sql.

Revision ID: 0f2176ad9045
Revises: e98cfc158897
Create Date: 2026-11-15 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
from alembic_utils.pg_function import PGFunction

# revision identifiers, used by Alembic.
revision: str = '0f2176ad9045'
down_revision: Union[str, Sequence[str], None] = 'e98cfc158897'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # replace_entity y no create_entity: en una BD desde cero, 88c353f63603 ejecuta
    # todos los app/funciones/*.sql y ya crea estas funciones.
    public_registrar_intento_inicio_sesion = PGFunction(
        schema="public",
        signature='registrar_intento_inicio_sesion(p_id_usuario integer, p_exitoso boolean)',
        definition='RETURNS integer\nLANGUAGE plpgsql\nAS $$\n-- Registra un intento de inicio de sesión (POST /auth/login) en log_inicio_sesion,\n-- tanto exitoso como fallido (Documentacion_BD\\: "Guarda cualquier intento").\n-- resultado\\: \'EXITOSO\' o \'FALLIDO\'. La API usa estos registros para bloquear la\n-- cuenta tras 5 intentos fallidos consecutivos.\nDECLARE\n    v_id_log integer;\nBEGIN\n    IF p_exitoso IS NULL THEN\n        RAISE EXCEPTION \'Falta indicar si el intento fue exitoso\';\n    END IF;\n\n    IF NOT EXISTS (SELECT 1 FROM usuario WHERE id_usuario = p_id_usuario) THEN\n        RAISE EXCEPTION \'El usuario % no existe\', p_id_usuario;\n    END IF;\n\n    INSERT INTO log_inicio_sesion (id_usuario, resultado, fecha)\n    VALUES (\n        p_id_usuario,\n        CASE WHEN p_exitoso THEN \'EXITOSO\' ELSE \'FALLIDO\' END,\n        localtimestamp\n    )\n    RETURNING id_log INTO v_id_log;\n\n    RETURN v_id_log;\nEND;\n$$'
    )
    op.replace_entity(public_registrar_intento_inicio_sesion)

    public_listar_intentos_inicio_sesion = PGFunction(
        schema="public",
        signature='listar_intentos_inicio_sesion(p_id_usuario integer, p_limite integer)',
        definition="RETURNS TABLE (\n    resultado              text,\n    segundos_transcurridos integer\n)\nLANGUAGE plpgsql\nSTABLE\nAS $$\n-- Últimos intentos de inicio de sesión de un usuario, del más reciente al más\n-- antiguo. segundos_transcurridos se calcula con el reloj de la BD (el mismo que\n-- guardó la fecha), así la API no depende de su propia zona horaria.\n#variable_conflict use_column\nBEGIN\n    IF p_limite IS NULL OR p_limite < 1 THEN\n        RAISE EXCEPTION 'El límite debe ser mayor que cero';\n    END IF;\n\n    RETURN QUERY\n    SELECT l.resultado,\n           floor(extract(epoch FROM (localtimestamp - l.fecha)))\\:\\:integer\n      FROM log_inicio_sesion l\n     WHERE l.id_usuario = p_id_usuario\n     ORDER BY l.fecha DESC, l.id_log DESC\n     LIMIT p_limite;\nEND;\n$$"
    )
    op.replace_entity(public_listar_intentos_inicio_sesion)


def downgrade() -> None:
    """Downgrade schema."""
    public_registrar_intento_inicio_sesion = PGFunction(
        schema="public",
        signature='registrar_intento_inicio_sesion(p_id_usuario integer, p_exitoso boolean)',
        definition='RETURNS integer\nLANGUAGE plpgsql\nAS $$\n-- Registra un intento de inicio de sesión (POST /auth/login) en log_inicio_sesion,\n-- tanto exitoso como fallido (Documentacion_BD\\: "Guarda cualquier intento").\n-- resultado\\: \'EXITOSO\' o \'FALLIDO\'. La API usa estos registros para bloquear la\n-- cuenta tras 5 intentos fallidos consecutivos.\nDECLARE\n    v_id_log integer;\nBEGIN\n    IF p_exitoso IS NULL THEN\n        RAISE EXCEPTION \'Falta indicar si el intento fue exitoso\';\n    END IF;\n\n    IF NOT EXISTS (SELECT 1 FROM usuario WHERE id_usuario = p_id_usuario) THEN\n        RAISE EXCEPTION \'El usuario % no existe\', p_id_usuario;\n    END IF;\n\n    INSERT INTO log_inicio_sesion (id_usuario, resultado, fecha)\n    VALUES (\n        p_id_usuario,\n        CASE WHEN p_exitoso THEN \'EXITOSO\' ELSE \'FALLIDO\' END,\n        localtimestamp\n    )\n    RETURNING id_log INTO v_id_log;\n\n    RETURN v_id_log;\nEND;\n$$'
    )
    op.drop_entity(public_registrar_intento_inicio_sesion)

    public_listar_intentos_inicio_sesion = PGFunction(
        schema="public",
        signature='listar_intentos_inicio_sesion(p_id_usuario integer, p_limite integer)',
        definition="RETURNS TABLE (\n    resultado              text,\n    segundos_transcurridos integer\n)\nLANGUAGE plpgsql\nSTABLE\nAS $$\n-- Últimos intentos de inicio de sesión de un usuario, del más reciente al más\n-- antiguo. segundos_transcurridos se calcula con el reloj de la BD (el mismo que\n-- guardó la fecha), así la API no depende de su propia zona horaria.\n#variable_conflict use_column\nBEGIN\n    IF p_limite IS NULL OR p_limite < 1 THEN\n        RAISE EXCEPTION 'El límite debe ser mayor que cero';\n    END IF;\n\n    RETURN QUERY\n    SELECT l.resultado,\n           floor(extract(epoch FROM (localtimestamp - l.fecha)))\\:\\:integer\n      FROM log_inicio_sesion l\n     WHERE l.id_usuario = p_id_usuario\n     ORDER BY l.fecha DESC, l.id_log DESC\n     LIMIT p_limite;\nEND;\n$$"
    )
    op.drop_entity(public_listar_intentos_inicio_sesion)
