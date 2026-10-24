CREATE OR REPLACE FUNCTION consultar_movimientos_por_cuenta(
    p_id_cuenta    integer,
    p_fecha_inicio date DEFAULT NULL,
    p_fecha_fin    date DEFAULT NULL
)
RETURNS TABLE (
    id_movimiento integer,
    fecha         date,
    descripcion   text,
    tipo          text,
    monto         numeric(12,2)
)
LANGUAGE plpgsql
STABLE
AS $$
#variable_conflict use_column
BEGIN
    IF NOT EXISTS (SELECT 1 FROM cuenta WHERE id_cuenta = p_id_cuenta) THEN
        RAISE EXCEPTION 'La cuenta % no existe', p_id_cuenta;
    END IF;
    IF p_fecha_inicio IS NOT NULL AND p_fecha_fin IS NOT NULL AND p_fecha_inicio > p_fecha_fin THEN
        RAISE EXCEPTION 'La fecha de inicio no puede ser posterior a la fecha final';
    END IF;

    RETURN QUERY
    SELECT m.id_movimiento, m.fecha, m.descripcion, mc.tipo, mc.monto
      FROM movimiento_cuenta mc
      JOIN movimiento m ON m.id_movimiento = mc.id_movimiento
     WHERE mc.id_cuenta = p_id_cuenta
       AND (p_fecha_inicio IS NULL OR m.fecha >= p_fecha_inicio)
       AND (p_fecha_fin    IS NULL OR m.fecha <= p_fecha_fin)
     ORDER BY m.fecha, m.id_movimiento, mc.id_movimiento_cuenta;
END;
$$;