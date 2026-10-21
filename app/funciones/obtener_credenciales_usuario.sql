-- obtener_credenciales_usuario
-- Uso: POST /auth/login
-- Parámetros: p_correo text
-- Retorna: TABLE (id_usuario integer, correo text, password_hash text, rol text, activo boolean)
-- Errores: 'El correo es obligatorio' si p_correo es NULL o vacío.
-- Si el correo no existe devuelve 0 filas (la API responde "credenciales inválidas").
-- Solo lee datos; no requiere transacción.
-- Invocación: SELECT * FROM obtener_credenciales_usuario(:correo);

CREATE OR REPLACE FUNCTION obtener_credenciales_usuario(p_correo text)
RETURNS TABLE (
    id_usuario    integer,
    correo        text,
    password_hash text,
    rol           text,
    activo        boolean
)
LANGUAGE plpgsql
STABLE
AS $$
#variable_conflict use_column
BEGIN
    IF coalesce(trim(p_correo), '') = '' THEN
        RAISE EXCEPTION 'El correo es obligatorio';
    END IF;

    RETURN QUERY
    SELECT u.id_usuario, u.correo, u.password_hash, r.nombre, u.activo
      FROM usuario u
      JOIN rol r ON r.id_rol = u.id_rol
     WHERE lower(u.correo) = lower(trim(p_correo));
END;
$$;