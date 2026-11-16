"""crear_cuenta_medico exige la cedula

FIX DE EMERGENCIA, revisar por BD. Hecho por Desarrollo (no por Base de Datos)
para corregir DEF-004: POST /auth/register solo pedia el numero de idoneidad,
que es publico en el directorio, y cualquiera podia crear la cuenta de otro
medico. Decision del lider (DECISIONES_CONFIRMADAS, seccion 1): idoneidad + cedula.
- crear_cuenta_medico pasa de (p_numero_idoneidad, p_correo, p_password_hash) a
  (p_numero_idoneidad, p_cedula, p_correo, p_password_hash). La cedula se compara
  sin espacios y en mayusculas. Si no coincide, el error es el mismo que cuando la
  idoneidad no existe.
- Se borra la firma anterior de 3 parametros para que no quede un camino que no
  pida la cedula; el downgrade la restaura tal como estaba (7813bd532a1f).
No cambia tablas. Base de Datos debe revisar y confirmar esta definicion.
Fuente: app/funciones/crear_cuenta_medico.sql.

Revision ID: 6668dd1b047b
Revises: e98cfc158897
Create Date: 2026-11-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from alembic_utils.pg_function import PGFunction

# revision identifiers, used by Alembic.
revision: str = '6668dd1b047b'
down_revision: Union[str, Sequence[str], None] = 'e98cfc158897'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # replace_entity y no create_entity: en una BD desde cero, 88c353f63603 ejecuta
    # todos los app/funciones/*.sql y ya crea estas funciones.
    public_crear_cuenta_medico = PGFunction(
        schema="public",
        signature='crear_cuenta_medico(p_numero_idoneidad text, p_cedula text, p_correo text, p_password_hash text)',
        definition="RETURNS integer\nLANGUAGE plpgsql\nAS $$\n-- DEF-004\\: la idoneidad es pública (directorio), así que además se exige la cédula\n-- del médico. Las dos se comparan sin espacios y en mayúsculas (8-123-456, PE-1-234).\n-- Si no coinciden, el error es el mismo que cuando la idoneidad no existe, para no\n-- revelar cuál de los dos datos falló.\nDECLARE\n    v_correo         text \\:= lower(btrim(p_correo));\n    v_id_medico      integer;\n    v_usuario_actual integer;\n    v_id_rol         integer;\n    v_id_usuario     integer;\nBEGIN\n    IF coalesce(btrim(p_numero_idoneidad), '') = '' THEN\n        RAISE EXCEPTION 'El número de idoneidad es obligatorio';\n    END IF;\n    IF coalesce(btrim(p_cedula), '') = '' THEN\n        RAISE EXCEPTION 'La cédula es obligatoria';\n    END IF;\n    IF v_correo IS NULL OR v_correo !~ '^[^@[\\:space\\:]]+@[^@[\\:space\\:]]+\\.[^@[\\:space\\:]]+$' THEN\n        RAISE EXCEPTION 'El correo no es válido';\n    END IF;\n    IF coalesce(p_password_hash, '') = '' THEN\n        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';\n    END IF;\n\n    SELECT m.id_medico, m.id_usuario\n      INTO v_id_medico, v_usuario_actual\n      FROM medico m\n     WHERE m.numero_idoneidad = btrim(p_numero_idoneidad)\n       AND upper(regexp_replace(m.cedula, '\\s', '', 'g'))\n         = upper(regexp_replace(p_cedula, '\\s', '', 'g'))\n       FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe un médico registrado con el número de idoneidad %', btrim(p_numero_idoneidad);\n    END IF;\n    IF v_usuario_actual IS NOT NULL THEN\n        RAISE EXCEPTION 'El médico ya tiene una cuenta de usuario';\n    END IF;\n    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN\n        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;\n    END IF;\n\n    SELECT r.id_rol INTO v_id_rol FROM rol r WHERE LOWER(BTRIM(r.nombre)) = 'medico';\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe el rol medico';\n    END IF;\n\n    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)\n    VALUES (v_id_rol, v_correo, p_password_hash, true, now())\n    RETURNING id_usuario INTO v_id_usuario;\n\n    UPDATE medico SET id_usuario = v_id_usuario WHERE id_medico = v_id_medico;\n\n    RETURN v_id_usuario;\nEND;\n$$"
    )
    op.replace_entity(public_crear_cuenta_medico)

    public_crear_cuenta_medico_anterior = PGFunction(
        schema="public",
        signature='crear_cuenta_medico(p_numero_idoneidad text, p_correo text, p_password_hash text)',
        definition="RETURNS integer\nLANGUAGE plpgsql\nAS $$\nDECLARE\n    v_correo         text \\:= lower(btrim(p_correo));\n    v_id_medico      integer;\n    v_usuario_actual integer;\n    v_id_rol         integer;\n    v_id_usuario     integer;\nBEGIN\n    IF coalesce(btrim(p_numero_idoneidad), '') = '' THEN\n        RAISE EXCEPTION 'El número de idoneidad es obligatorio';\n    END IF;\n    IF v_correo IS NULL OR v_correo !~ '^[^@[\\:space\\:]]+@[^@[\\:space\\:]]+\\.[^@[\\:space\\:]]+$' THEN\n        RAISE EXCEPTION 'El correo no es válido';\n    END IF;\n    IF coalesce(p_password_hash, '') = '' THEN\n        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';\n    END IF;\n\n    SELECT m.id_medico, m.id_usuario\n      INTO v_id_medico, v_usuario_actual\n      FROM medico m\n     WHERE m.numero_idoneidad = btrim(p_numero_idoneidad)\n       FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe un médico registrado con el número de idoneidad %', btrim(p_numero_idoneidad);\n    END IF;\n    IF v_usuario_actual IS NOT NULL THEN\n        RAISE EXCEPTION 'El médico ya tiene una cuenta de usuario';\n    END IF;\n    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN\n        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;\n    END IF;\n\n    SELECT r.id_rol INTO v_id_rol FROM rol r WHERE LOWER(BTRIM(r.nombre)) = 'medico';\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe el rol medico';\n    END IF;\n\n    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)\n    VALUES (v_id_rol, v_correo, p_password_hash, true, now())\n    RETURNING id_usuario INTO v_id_usuario;\n\n    UPDATE medico SET id_usuario = v_id_usuario WHERE id_medico = v_id_medico;\n\n    RETURN v_id_usuario;\nEND;\n$$"
    )
    op.drop_entity(public_crear_cuenta_medico_anterior)


def downgrade() -> None:
    """Downgrade schema."""
    public_crear_cuenta_medico = PGFunction(
        schema="public",
        signature='crear_cuenta_medico(p_numero_idoneidad text, p_cedula text, p_correo text, p_password_hash text)',
        definition="RETURNS integer\nLANGUAGE plpgsql\nAS $$\n-- DEF-004\\: la idoneidad es pública (directorio), así que además se exige la cédula\n-- del médico. Las dos se comparan sin espacios y en mayúsculas (8-123-456, PE-1-234).\n-- Si no coinciden, el error es el mismo que cuando la idoneidad no existe, para no\n-- revelar cuál de los dos datos falló.\nDECLARE\n    v_correo         text \\:= lower(btrim(p_correo));\n    v_id_medico      integer;\n    v_usuario_actual integer;\n    v_id_rol         integer;\n    v_id_usuario     integer;\nBEGIN\n    IF coalesce(btrim(p_numero_idoneidad), '') = '' THEN\n        RAISE EXCEPTION 'El número de idoneidad es obligatorio';\n    END IF;\n    IF coalesce(btrim(p_cedula), '') = '' THEN\n        RAISE EXCEPTION 'La cédula es obligatoria';\n    END IF;\n    IF v_correo IS NULL OR v_correo !~ '^[^@[\\:space\\:]]+@[^@[\\:space\\:]]+\\.[^@[\\:space\\:]]+$' THEN\n        RAISE EXCEPTION 'El correo no es válido';\n    END IF;\n    IF coalesce(p_password_hash, '') = '' THEN\n        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';\n    END IF;\n\n    SELECT m.id_medico, m.id_usuario\n      INTO v_id_medico, v_usuario_actual\n      FROM medico m\n     WHERE m.numero_idoneidad = btrim(p_numero_idoneidad)\n       AND upper(regexp_replace(m.cedula, '\\s', '', 'g'))\n         = upper(regexp_replace(p_cedula, '\\s', '', 'g'))\n       FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe un médico registrado con el número de idoneidad %', btrim(p_numero_idoneidad);\n    END IF;\n    IF v_usuario_actual IS NOT NULL THEN\n        RAISE EXCEPTION 'El médico ya tiene una cuenta de usuario';\n    END IF;\n    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN\n        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;\n    END IF;\n\n    SELECT r.id_rol INTO v_id_rol FROM rol r WHERE LOWER(BTRIM(r.nombre)) = 'medico';\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe el rol medico';\n    END IF;\n\n    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)\n    VALUES (v_id_rol, v_correo, p_password_hash, true, now())\n    RETURNING id_usuario INTO v_id_usuario;\n\n    UPDATE medico SET id_usuario = v_id_usuario WHERE id_medico = v_id_medico;\n\n    RETURN v_id_usuario;\nEND;\n$$"
    )
    op.drop_entity(public_crear_cuenta_medico)

    public_crear_cuenta_medico_anterior = PGFunction(
        schema="public",
        signature='crear_cuenta_medico(p_numero_idoneidad text, p_correo text, p_password_hash text)',
        definition="RETURNS integer\nLANGUAGE plpgsql\nAS $$\nDECLARE\n    v_correo         text \\:= lower(btrim(p_correo));\n    v_id_medico      integer;\n    v_usuario_actual integer;\n    v_id_rol         integer;\n    v_id_usuario     integer;\nBEGIN\n    IF coalesce(btrim(p_numero_idoneidad), '') = '' THEN\n        RAISE EXCEPTION 'El número de idoneidad es obligatorio';\n    END IF;\n    IF v_correo IS NULL OR v_correo !~ '^[^@[\\:space\\:]]+@[^@[\\:space\\:]]+\\.[^@[\\:space\\:]]+$' THEN\n        RAISE EXCEPTION 'El correo no es válido';\n    END IF;\n    IF coalesce(p_password_hash, '') = '' THEN\n        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';\n    END IF;\n\n    SELECT m.id_medico, m.id_usuario\n      INTO v_id_medico, v_usuario_actual\n      FROM medico m\n     WHERE m.numero_idoneidad = btrim(p_numero_idoneidad)\n       FOR UPDATE;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe un médico registrado con el número de idoneidad %', btrim(p_numero_idoneidad);\n    END IF;\n    IF v_usuario_actual IS NOT NULL THEN\n        RAISE EXCEPTION 'El médico ya tiene una cuenta de usuario';\n    END IF;\n    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN\n        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;\n    END IF;\n\n    SELECT r.id_rol INTO v_id_rol FROM rol r WHERE LOWER(BTRIM(r.nombre)) = 'medico';\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe el rol medico';\n    END IF;\n\n    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)\n    VALUES (v_id_rol, v_correo, p_password_hash, true, now())\n    RETURNING id_usuario INTO v_id_usuario;\n\n    UPDATE medico SET id_usuario = v_id_usuario WHERE id_medico = v_id_medico;\n\n    RETURN v_id_usuario;\nEND;\n$$"
    )
    op.replace_entity(public_crear_cuenta_medico_anterior)
