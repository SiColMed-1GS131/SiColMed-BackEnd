CREATE OR REPLACE FUNCTION crear_cuenta(p_nombre text, p_tipo text)
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE v_id integer;
BEGIN
  IF upper(btrim(p_tipo)) NOT IN ('DEBITO','CREDITO') THEN
    RAISE EXCEPTION 'El tipo de cuenta debe ser DEBITO o CREDITO';
  END IF;
  INSERT INTO cuenta (nombre, tipo, activa) VALUES (btrim(p_nombre), upper(btrim(p_tipo)), true)
  RETURNING id_cuenta INTO v_id;
  RETURN v_id;
END $$;
