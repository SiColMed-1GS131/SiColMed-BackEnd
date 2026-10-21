-- DISEÑO PENDIENTE (decisión 5): esta versión recibe las líneas del asiento como JSON.
CREATE OR REPLACE FUNCTION registrar_movimiento(
    p_fecha       date,
    p_descripcion text,
    p_detalle     jsonb
)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_fecha        date := coalesce(p_fecha, CURRENT_DATE);
    v_lineas       integer;
    v_invalidas    integer;
    v_debitos_n    integer;
    v_creditos_n   integer;
    v_cuentas_mal  integer;
    v_debitos      numeric;
    v_creditos     numeric;
    v_id           integer;
BEGIN
    -- p_detalle = [{"id_cuenta": 1, "monto": 50.00, "tipo": "DEBITO"}, ...]
    IF p_detalle IS NULL OR jsonb_typeof(p_detalle) <> 'array' THEN
        RAISE EXCEPTION 'El detalle debe ser un arreglo JSON de líneas';
    END IF;

    SELECT count(*),
           count(*) FILTER (WHERE l.id_cuenta IS NULL OR l.monto IS NULL OR round(l.monto, 2) <= 0
                               OR l.tipo IS NULL
                               OR upper(btrim(l.tipo)) NOT IN ('DEBITO', 'CREDITO')),
           count(*) FILTER (WHERE upper(btrim(l.tipo)) = 'DEBITO'),
           count(*) FILTER (WHERE upper(btrim(l.tipo)) = 'CREDITO'),
           count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM cuenta c
                                               WHERE c.id_cuenta = l.id_cuenta AND c.activa)),
           coalesce(sum(round(l.monto, 2)) FILTER (WHERE upper(btrim(l.tipo)) = 'DEBITO'), 0),
           coalesce(sum(round(l.monto, 2)) FILTER (WHERE upper(btrim(l.tipo)) = 'CREDITO'), 0)
      INTO v_lineas, v_invalidas, v_debitos_n, v_creditos_n, v_cuentas_mal, v_debitos, v_creditos
      FROM jsonb_to_recordset(p_detalle) AS l(id_cuenta integer, monto numeric, tipo text);

    IF v_lineas < 2 THEN
        RAISE EXCEPTION 'Un movimiento necesita al menos dos líneas';
    END IF;
    IF v_invalidas > 0 THEN
        RAISE EXCEPTION 'Cada línea debe tener cuenta, monto mayor que cero y tipo DEBITO o CREDITO';
    END IF;
    IF v_debitos_n = 0 OR v_creditos_n = 0 THEN
        RAISE EXCEPTION 'El movimiento debe tener al menos una línea de débito y una de crédito';
    END IF;
    IF v_cuentas_mal > 0 THEN
        RAISE EXCEPTION 'Hay cuentas que no existen o están inactivas';
    END IF;
    IF v_debitos <> v_creditos THEN
        RAISE EXCEPTION 'El movimiento no cuadra: débitos = %, créditos = %', v_debitos, v_creditos;
    END IF;

    INSERT INTO movimiento (fecha, descripcion)
    VALUES (v_fecha, p_descripcion)
    RETURNING id_movimiento INTO v_id;

    INSERT INTO movimiento_cuenta (id_movimiento, id_cuenta, monto, tipo)
    SELECT v_id, l.id_cuenta, round(l.monto, 2), upper(btrim(l.tipo))
      FROM jsonb_to_recordset(p_detalle) AS l(id_cuenta integer, monto numeric, tipo text);

    RETURN v_id;
END;
$$;