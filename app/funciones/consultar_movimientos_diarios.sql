CREATE OR REPLACE FUNCTION consultar_movimientos_diarios(p_fecha date)
RETURNS TABLE (
    id_movimiento integer,
    fecha         date,
    descripcion   text,
    id_cuenta     integer,
    nombre_cuenta text,
    tipo          text,
    monto         numeric(12,2)
)
LANGUAGE plpgsql
STABLE
AS $$
#variable_conflict use_column
BEGIN
    IF p_fecha IS NULL THEN
        RAISE EXCEPTION 'La fecha es obligatoria';
    END IF;

    RETURN QUERY
    SELECT m.id_movimiento, m.fecha, m.descripcion,
           c.id_cuenta, c.nombre, mc.tipo, mc.monto
      FROM movimiento m
      JOIN movimiento_cuenta mc ON mc.id_movimiento = m.id_movimiento
      JOIN cuenta c             ON c.id_cuenta = mc.id_cuenta
     WHERE m.fecha = p_fecha
     ORDER BY m.id_movimiento, mc.tipo DESC, mc.id_movimiento_cuenta;
END;
$$;