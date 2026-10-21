CREATE OR REPLACE FUNCTION eliminar_cuenta(p_id_cuenta integer)
RETURNS text
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM 1 FROM cuenta WHERE id_cuenta = p_id_cuenta FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'La cuenta % no existe', p_id_cuenta;
    END IF;

    IF EXISTS (SELECT 1 FROM movimiento_cuenta WHERE id_cuenta = p_id_cuenta) THEN
        UPDATE cuenta SET activa = false WHERE id_cuenta = p_id_cuenta;
        RETURN 'DESACTIVADA';
    END IF;

    DELETE FROM cuenta WHERE id_cuenta = p_id_cuenta;
    RETURN 'ELIMINADA';
END;
$$;