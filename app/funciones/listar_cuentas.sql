CREATE OR REPLACE FUNCTION listar_cuentas(p_activa boolean DEFAULT NULL)
RETURNS TABLE (id_cuenta integer, nombre text, tipo text, activa boolean, tiene_movimientos boolean)
LANGUAGE sql STABLE AS $$
  SELECT c.id_cuenta, c.nombre, c.tipo, c.activa,
         EXISTS (SELECT 1 FROM movimiento_cuenta mc WHERE mc.id_cuenta = c.id_cuenta)
    FROM cuenta c
   WHERE p_activa IS NULL OR c.activa = p_activa
   ORDER BY c.nombre;
$$;
