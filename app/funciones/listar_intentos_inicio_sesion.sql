CREATE OR REPLACE FUNCTION listar_intentos_inicio_sesion(
    p_id_usuario integer,
    p_limite     integer
)
RETURNS TABLE (
    resultado              text,
    segundos_transcurridos integer
)
LANGUAGE plpgsql
STABLE
AS $$
-- Últimos intentos de inicio de sesión de un usuario, del más reciente al más
-- antiguo. segundos_transcurridos se calcula con el reloj de la BD (el mismo que
-- guardó la fecha), así la API no depende de su propia zona horaria.
#variable_conflict use_column
BEGIN
    IF p_limite IS NULL OR p_limite < 1 THEN
        RAISE EXCEPTION 'El límite debe ser mayor que cero';
    END IF;

    RETURN QUERY
    SELECT l.resultado,
           floor(extract(epoch FROM (localtimestamp - l.fecha)))::integer
      FROM log_inicio_sesion l
     WHERE l.id_usuario = p_id_usuario
     ORDER BY l.fecha DESC, l.id_log DESC
     LIMIT p_limite;
END;
$$;
