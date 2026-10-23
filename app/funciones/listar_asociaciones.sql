CREATE OR REPLACE FUNCTION listar_asociaciones()
RETURNS TABLE (
    id_asociacion INTEGER,
    nombre TEXT
)
LANGUAGE sql
STABLE
AS $$
    SELECT a.id_asociacion, a.nombre
    FROM asociacion AS a
    ORDER BY a.nombre ASC;
$$;