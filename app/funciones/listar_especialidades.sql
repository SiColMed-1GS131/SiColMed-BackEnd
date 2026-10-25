CREATE OR REPLACE FUNCTION listar_especialidades()
RETURNS TABLE (
    id_especialidad INTEGER,
    nombre TEXT
)
LANGUAGE sql
STABLE
AS $$
    SELECT e.id_especialidad, e.nombre
    FROM especialidad AS e
    ORDER BY e.nombre ASC;
$$;