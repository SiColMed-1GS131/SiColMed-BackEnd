CREATE OR REPLACE FUNCTION calcular_balance_general(
    p_fecha_inicio date,
    p_fecha_fin    date
)
RETURNS TABLE (
    id_cuenta     integer,
    nombre_cuenta text,
    total_debito  numeric(12,2),
    total_credito numeric(12,2),
    saldo         numeric(12,2)
)
LANGUAGE plpgsql
STABLE
AS $$
#variable_conflict use_column
BEGIN
    IF p_fecha_inicio IS NULL OR p_fecha_fin IS NULL THEN
        RAISE EXCEPTION 'La fecha de inicio y la fecha final son obligatorias';
    END IF;
    IF p_fecha_inicio > p_fecha_fin THEN
        RAISE EXCEPTION 'La fecha de inicio no puede ser posterior a la fecha final';
    END IF;

    RETURN QUERY
    WITH totales AS (
        SELECT mc.id_cuenta,
               sum(mc.monto) FILTER (WHERE mc.tipo = 'DEBITO')  AS deb,
               sum(mc.monto) FILTER (WHERE mc.tipo = 'CREDITO') AS cre
          FROM movimiento_cuenta mc
          JOIN movimiento m ON m.id_movimiento = mc.id_movimiento
         WHERE m.fecha BETWEEN p_fecha_inicio AND p_fecha_fin
         GROUP BY mc.id_cuenta
    )
    SELECT c.id_cuenta,
           c.nombre,
           coalesce(t.deb, 0)::numeric(12,2),
           coalesce(t.cre, 0)::numeric(12,2),
           (CASE WHEN c.tipo = 'DEBITO'
                 THEN coalesce(t.deb, 0) - coalesce(t.cre, 0)
                 ELSE coalesce(t.cre, 0) - coalesce(t.deb, 0) END)::numeric(12,2)
      FROM cuenta c
      LEFT JOIN totales t ON t.id_cuenta = c.id_cuenta
     WHERE c.activa OR t.id_cuenta IS NOT NULL
     ORDER BY c.id_cuenta;
END;
$$;