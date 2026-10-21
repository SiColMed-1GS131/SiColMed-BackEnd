-- obtener_usuario_por_id
-- Uso: GET /auth/me
-- Parámetros: p_id_usuario integer
-- Retorna: TABLE (id_usuario integer, nombre text, correo text,numero_idoneidad text, rol text, activo boolean)
-- Errores: 'El id de usuario es obligatorio' si p_id_usuario es NULL.
-- Si el usuario no existe devuelve 0 filas.
-- nombre y numero_idoneidad salen de MEDICO; para usuarios que no son médicos vienen NULL.
-- No devuelve password_hash. Solo lee datos; no requiere transacción.
-- Invocación: SELECT * FROM obtener_usuario_por_id(:id_usuario);

CREATE OR REPLACE FUNCTION obtener_usuario_por_id(p_id_usuario integer)
RETURNS TABLE (
    id_usuario       integer,
    nombre           text,
    correo           text,
    numero_idoneidad text,
    rol              text,
    activo           boolean
)
LANGUAGE plpgsql
STABLE
AS $$
#variable_conflict use_column
BEGIN
    IF p_id_usuario IS NULL THEN
        RAISE EXCEPTION 'El id de usuario es obligatorio';
    END IF;

    RETURN QUERY
    SELECT u.id_usuario,
           nullif(concat_ws(' ', m.primer_nombre, m.segundo_nombre,
                                 m.apellido_paterno, m.apellido_materno), ''),
           u.correo,
           m.numero_idoneidad,
           r.nombre,
           u.activo
      FROM usuario u
      JOIN rol r         ON r.id_rol = u.id_rol
      LEFT JOIN medico m ON m.id_usuario = u.id_usuario
     WHERE u.id_usuario = p_id_usuario;
END;
$$;