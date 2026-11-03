"""agrega codigo oficial a provincia, distrito y corregimiento

FIX DE EMERGENCIA hecho por Desarrollo (no por Base de Datos): agrega la
columna `codigo` (texto, opcional, única) a provincia, distrito y
corregimiento para guardar el código oficial de la División Política
Administrativa 2025 de ANATI/INEC (ej. provincia "08", distrito "0808",
corregimiento "080812").

Por qué hace falta: los nombres no identifican una unidad (hay distritos y
corregimientos con el mismo nombre en lugares distintos) y la tarea exige
conservar los códigos oficiales. app/scripts/seed_catalogos.py usa el código
para no duplicar registros al ejecutarse varias veces.

Es opcional para no romper las filas que ya existen; seed_catalogos le asigna
el código a la fila existente que coincide por nombre dentro de su unidad
superior. No cambia nombres de tablas, columnas, claves primarias ni foráneas.
Base de Datos debe revisar y confirmar este cambio.

Revision ID: 5d1f0c7a9e42
Revises: 8b0b492d3623
Create Date: 2026-11-03 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d1f0c7a9e42'
down_revision: Union[str, Sequence[str], None] = '8b0b492d3623'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLAS = ("provincia", "distrito", "corregimiento")


def upgrade() -> None:
    """Upgrade schema."""
    for tabla in TABLAS:
        op.add_column(tabla, sa.Column("codigo", sa.Text(), nullable=True))
        op.create_unique_constraint(f"uq_{tabla}_codigo", tabla, ["codigo"])


def downgrade() -> None:
    """Downgrade schema."""
    for tabla in reversed(TABLAS):
        op.drop_constraint(f"uq_{tabla}_codigo", tabla, type_="unique")
        op.drop_column(tabla, "codigo")
