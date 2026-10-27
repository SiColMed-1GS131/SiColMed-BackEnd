CREATE OR REPLACE FUNCTION listar_subespecialidades(
    p_id_especialidad INTEGER DEFAULT NULL
)
RETURNS TABLE (
    id_subespecialidad INTEGER,
    id_especialidad INTEGER,
    nombre TEXT
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        s.id_subespecialidad,
        s.id_especialidad,
        s.nombre
    FROM subespecialidad AS s
    WHERE p_id_especialidad IS NULL
       OR s.id_especialidad = p_id_especialidad
    ORDER BY s.nombre ASC;
$$;