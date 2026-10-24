CREATE OR REPLACE FUNCTION editar_cuenta(
    p_id_cuenta integer,
    p_nombre    text    DEFAULT NULL,
    p_tipo      text    DEFAULT NULL,
    p_activa    boolean DEFAULT NULL
)
RETURNS boolean
LANGUAGE plpgsql
AS $$
DECLARE
    v_nombre text := nullif(btrim(p_nombre), '');
    v_tipo   text := upper(nullif(btrim(p_tipo), ''));
    v_cuenta cuenta%ROWTYPE;
BEGIN
    IF v_nombre IS NULL AND v_tipo IS NULL AND p_activa IS NULL THEN
        RAISE EXCEPTION 'Debe indicar al menos un dato a modificar';
    END IF;
    IF v_tipo IS NOT NULL AND v_tipo NOT IN ('DEBITO', 'CREDITO') THEN
        RAISE EXCEPTION 'El tipo de cuenta debe ser DEBITO o CREDITO';
    END IF;

    SELECT * INTO v_cuenta FROM cuenta WHERE id_cuenta = p_id_cuenta FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'La cuenta % no existe', p_id_cuenta;
    END IF;

    IF v_tipo IS NOT NULL AND v_tipo <> v_cuenta.tipo
       AND EXISTS (SELECT 1 FROM movimiento_cuenta WHERE id_cuenta = p_id_cuenta) THEN
        RAISE EXCEPTION 'No se puede cambiar el tipo de una cuenta que ya tiene movimientos';
    END IF;
    IF v_nombre IS NOT NULL
       AND EXISTS (SELECT 1 FROM cuenta
                    WHERE lower(nombre) = lower(v_nombre) AND id_cuenta <> p_id_cuenta) THEN
        RAISE EXCEPTION 'Ya existe una cuenta con el nombre %', v_nombre;
    END IF;

    UPDATE cuenta
       SET nombre = coalesce(v_nombre, nombre),
           tipo   = coalesce(v_tipo, tipo),
           activa = coalesce(p_activa, activa)
     WHERE id_cuenta = p_id_cuenta;

    RETURN true;
END;
$$;