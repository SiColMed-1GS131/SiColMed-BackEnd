from pathlib import Path
from alembic import op


revision = "88c353f63603"
down_revision = "29d469811429"
branch_labels = None
depends_on = None


def upgrade() -> None:
    carpeta_funciones = Path(__file__).resolve().parents[2] / "app" / "funciones"

    archivos = sorted(carpeta_funciones.glob("*.sql"))

    if not archivos:
        raise RuntimeError(
            f"No se encontraron archivos SQL en {carpeta_funciones}"
        )

    for archivo in archivos:
        sql = archivo.read_text(encoding="utf-8").strip()
        if sql:
            op.get_bind().connection.cursor().execute(sql)

def downgrade() -> None:
    op.get_bind().exec_driver_sql("""
        DROP FUNCTION IF EXISTS registrar_movimiento(date, text, jsonb);
        DROP FUNCTION IF EXISTS registrar_medico(
            text, text, text, text, text, date,
            text, text, text, text, text, text,
            text, text, text, integer
        );
        DROP FUNCTION IF EXISTS procesar_solicitud_cambio(
            integer, integer, jsonb, text
        );
        DROP FUNCTION IF EXISTS obtener_usuario_por_id(integer);
        DROP FUNCTION IF EXISTS obtener_perfil_medico(integer);
        DROP FUNCTION IF EXISTS obtener_credenciales_usuario(text);
        DROP FUNCTION IF EXISTS listar_solicitudes_cambio(text);
        DROP FUNCTION IF EXISTS filtrar_medicos(
            text, integer, integer, integer, boolean, integer, text,
            integer, integer
        );
        DROP FUNCTION IF EXISTS eliminar_cuenta(integer);
        DROP FUNCTION IF EXISTS editar_cuenta(integer, text, text, boolean);
        DROP FUNCTION IF EXISTS crear_solicitud_cambio(integer, jsonb);
        DROP FUNCTION IF EXISTS crear_cuenta_medico(text, text, text);
        DROP FUNCTION IF EXISTS consultar_movimientos_por_cuenta(integer, date, date);
        DROP FUNCTION IF EXISTS consultar_movimientos_diarios(date);
        DROP FUNCTION IF EXISTS calcular_balance_general(date, date);
        DROP FUNCTION IF EXISTS actualizar_medico(integer, integer, jsonb);
    """)