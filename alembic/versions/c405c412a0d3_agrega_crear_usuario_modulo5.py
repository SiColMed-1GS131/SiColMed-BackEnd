"""agrega crear_usuario_modulo5

FIX DE EMERGENCIA, revisar por BD. Hecho por Desarrollo (no por Base de Datos)
para corregir DEF-009: el Modulo 5 lo usan el Tesorero y el Administrador de la
Asociacion (RQ-5.R), pero ninguna funcion creaba usuarios de esos roles y no habia
usuarios de prueba. docs/datos-prueba.md pedia una funcion de alta en vez de
insertar directo en usuario.
- crear_usuario_modulo5(p_correo, p_password_hash, p_rol, p_id_administrador):
  solo roles tesorero y admin_asociacion; la crea un admin_cmp activo; correo
  unico; registra CREAR_USUARIO_MODULO5 en auditoria. Mismas reglas que
  crear_usuario_admin.
- Limitacion: usuario no tiene relacion con asociacion, asi que un
  admin_asociacion no indica que asociacion administra.
No cambia tablas. Base de Datos debe revisar y confirmar esta definicion.
Fuente: app/funciones/crear_usuario_modulo5.sql.

Revision ID: c405c412a0d3
Revises: e98cfc158897
Create Date: 2026-11-16 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from alembic_utils.pg_function import PGFunction

# revision identifiers, used by Alembic.
revision: str = 'c405c412a0d3'
down_revision: Union[str, Sequence[str], None] = 'e98cfc158897'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # replace_entity y no create_entity: en una BD desde cero, 88c353f63603 ejecuta
    # todos los app/funciones/*.sql y ya crea estas funciones.
    public_crear_usuario_modulo5 = PGFunction(
        schema="public",
        signature='crear_usuario_modulo5(p_correo text, p_password_hash text, p_rol text, p_id_administrador integer)',
        definition="RETURNS integer\nLANGUAGE plpgsql\nAS $$\n-- DEF-009\\: alta de los usuarios del Módulo 5 (tesorero y admin_asociacion), que ninguna\n-- función creaba. Mismas reglas que crear_usuario_admin\\: la cuenta la crea un\n-- administrador activo (admin_cmp), el correo es único y el alta queda en auditoria.\n-- Limitación\\: usuario no tiene relación con asociacion, así que un admin_asociacion no\n-- indica qué asociación administra (además, el catálogo de asociaciones está vacío).\nDECLARE\n    v_correo     text \\:= lower(btrim(p_correo));\n    v_rol        text \\:= lower(btrim(p_rol));\n    v_id_rol       integer;\n    v_id_rol_admin integer;\n    v_id_usuario   integer;\nBEGIN\n    IF v_correo IS NULL OR v_correo !~ '^[^@[\\:space\\:]]+@[^@[\\:space\\:]]+\\.[^@[\\:space\\:]]+$' THEN\n        RAISE EXCEPTION 'El correo no es valido';\n    END IF;\n    IF coalesce(p_password_hash, '') = '' THEN\n        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';\n    END IF;\n    IF v_rol IS NULL OR v_rol NOT IN ('tesorero', 'admin_asociacion') THEN\n        RAISE EXCEPTION 'El rol debe ser tesorero o admin_asociacion';\n    END IF;\n\n    SELECT r.id_rol\n      INTO v_id_rol\n      FROM rol r\n     WHERE lower(btrim(r.nombre)) = v_rol\n     ORDER BY r.id_rol\n     LIMIT 1;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe el rol %', v_rol;\n    END IF;\n\n    SELECT u.id_rol\n      INTO v_id_rol_admin\n      FROM usuario u\n      JOIN rol r ON r.id_rol = u.id_rol\n     WHERE u.id_usuario = p_id_administrador\n       AND u.activo\n       AND lower(btrim(r.nombre)) = 'admin_cmp';\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'El usuario % no existe, está inactivo o no es administrador', p_id_administrador;\n    END IF;\n\n    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN\n        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;\n    END IF;\n\n    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)\n    VALUES (v_id_rol, v_correo, p_password_hash, true, now())\n    RETURNING id_usuario INTO v_id_usuario;\n\n    INSERT INTO auditoria (id_usuario, id_rol, accion, entidad, id_registro, fecha_hora, descripcion)\n    VALUES (p_id_administrador, v_id_rol_admin, 'CREAR_USUARIO_MODULO5', 'USUARIO',\n            v_id_usuario, now(), 'Usuario ' || v_rol || ' ' || v_correo || ' creado');\n\n    RETURN v_id_usuario;\nEND;\n$$"
    )
    op.replace_entity(public_crear_usuario_modulo5)


def downgrade() -> None:
    """Downgrade schema."""
    public_crear_usuario_modulo5 = PGFunction(
        schema="public",
        signature='crear_usuario_modulo5(p_correo text, p_password_hash text, p_rol text, p_id_administrador integer)',
        definition="RETURNS integer\nLANGUAGE plpgsql\nAS $$\n-- DEF-009\\: alta de los usuarios del Módulo 5 (tesorero y admin_asociacion), que ninguna\n-- función creaba. Mismas reglas que crear_usuario_admin\\: la cuenta la crea un\n-- administrador activo (admin_cmp), el correo es único y el alta queda en auditoria.\n-- Limitación\\: usuario no tiene relación con asociacion, así que un admin_asociacion no\n-- indica qué asociación administra (además, el catálogo de asociaciones está vacío).\nDECLARE\n    v_correo     text \\:= lower(btrim(p_correo));\n    v_rol        text \\:= lower(btrim(p_rol));\n    v_id_rol       integer;\n    v_id_rol_admin integer;\n    v_id_usuario   integer;\nBEGIN\n    IF v_correo IS NULL OR v_correo !~ '^[^@[\\:space\\:]]+@[^@[\\:space\\:]]+\\.[^@[\\:space\\:]]+$' THEN\n        RAISE EXCEPTION 'El correo no es valido';\n    END IF;\n    IF coalesce(p_password_hash, '') = '' THEN\n        RAISE EXCEPTION 'El hash de la contraseña es obligatorio';\n    END IF;\n    IF v_rol IS NULL OR v_rol NOT IN ('tesorero', 'admin_asociacion') THEN\n        RAISE EXCEPTION 'El rol debe ser tesorero o admin_asociacion';\n    END IF;\n\n    SELECT r.id_rol\n      INTO v_id_rol\n      FROM rol r\n     WHERE lower(btrim(r.nombre)) = v_rol\n     ORDER BY r.id_rol\n     LIMIT 1;\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'No existe el rol %', v_rol;\n    END IF;\n\n    SELECT u.id_rol\n      INTO v_id_rol_admin\n      FROM usuario u\n      JOIN rol r ON r.id_rol = u.id_rol\n     WHERE u.id_usuario = p_id_administrador\n       AND u.activo\n       AND lower(btrim(r.nombre)) = 'admin_cmp';\n    IF NOT FOUND THEN\n        RAISE EXCEPTION 'El usuario % no existe, está inactivo o no es administrador', p_id_administrador;\n    END IF;\n\n    IF EXISTS (SELECT 1 FROM usuario WHERE lower(correo) = v_correo) THEN\n        RAISE EXCEPTION 'El correo % ya está registrado', v_correo;\n    END IF;\n\n    INSERT INTO usuario (id_rol, correo, password_hash, activo, fecha_creacion)\n    VALUES (v_id_rol, v_correo, p_password_hash, true, now())\n    RETURNING id_usuario INTO v_id_usuario;\n\n    INSERT INTO auditoria (id_usuario, id_rol, accion, entidad, id_registro, fecha_hora, descripcion)\n    VALUES (p_id_administrador, v_id_rol_admin, 'CREAR_USUARIO_MODULO5', 'USUARIO',\n            v_id_usuario, now(), 'Usuario ' || v_rol || ' ' || v_correo || ' creado');\n\n    RETURN v_id_usuario;\nEND;\n$$"
    )
    op.drop_entity(public_crear_usuario_modulo5)
