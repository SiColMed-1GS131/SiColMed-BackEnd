"""agrega funciones listar_cuentas y crear_cuenta

FIX DE EMERGENCIA hecho por Desarrollo (no por Base de Datos): GET y POST
/cuentas respondían 400 porque estas funciones no existían. Base de Datos
debe revisar y confirmar estas definiciones. Fuente: app/funciones/
listar_cuentas.sql y crear_cuenta.sql.

Revision ID: 0b02962cab9d
Revises: 92560798e0f3
Create Date: 2026-11-03 05:28:16.858062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic_utils.pg_function import PGFunction


# revision identifiers, used by Alembic.
revision: str = '0b02962cab9d'
down_revision: Union[str, Sequence[str], None] = '92560798e0f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


public_listar_cuentas = PGFunction(
    schema="public",
    signature="listar_cuentas(p_activa boolean DEFAULT NULL)",
    definition="RETURNS TABLE (id_cuenta integer, nombre text, tipo text, activa boolean, tiene_movimientos boolean)\nLANGUAGE sql STABLE AS $$\n  SELECT c.id_cuenta, c.nombre, c.tipo, c.activa,\n         EXISTS (SELECT 1 FROM movimiento_cuenta mc WHERE mc.id_cuenta = c.id_cuenta)\n    FROM cuenta c\n   WHERE p_activa IS NULL OR c.activa = p_activa\n   ORDER BY c.nombre;\n$$"
)

public_crear_cuenta = PGFunction(
    schema="public",
    signature="crear_cuenta(p_nombre text, p_tipo text)",
    definition="RETURNS integer LANGUAGE plpgsql AS $$\nDECLARE v_id integer;\nBEGIN\n  IF upper(btrim(p_tipo)) NOT IN ('DEBITO','CREDITO') THEN\n    RAISE EXCEPTION 'El tipo de cuenta debe ser DEBITO o CREDITO';\n  END IF;\n  INSERT INTO cuenta (nombre, tipo, activa) VALUES (btrim(p_nombre), upper(btrim(p_tipo)), true)\n  RETURNING id_cuenta INTO v_id;\n  RETURN v_id;\nEND $$"
)


def upgrade() -> None:
    """Upgrade schema."""
    # replace_entity (CREATE OR REPLACE) y no create_entity: en una BD desde cero,
    # la migración 88c353f63603 ejecuta todos los app/funciones/*.sql que existan
    # en ese momento y ya crea estas dos funciones. En una BD que pasó por
    # 88c353f63603 antes de que existieran los .sql, aquí se crean.
    op.replace_entity(public_listar_cuentas)
    op.replace_entity(public_crear_cuenta)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_entity(public_crear_cuenta)
    op.drop_entity(public_listar_cuentas)
