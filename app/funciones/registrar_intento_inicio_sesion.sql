CREATE OR REPLACE FUNCTION registrar_intento_inicio_sesion(
    p_id_usuario integer,
    p_exitoso    boolean
)
RETURNS integer
LANGUAGE plpgsql
AS $$
-- Registra un intento de inicio de sesión (POST /auth/login) en log_inicio_sesion,
-- tanto exitoso como fallido (Documentacion_BD: "Guarda cualquier intento").
-- resultado: 'EXITOSO' o 'FALLIDO'. La API usa estos registros para bloquear la
-- cuenta tras 5 intentos fallidos consecutivos.
DECLARE
    v_id_log integer;
BEGIN
    IF p_exitoso IS NULL THEN
        RAISE EXCEPTION 'Falta indicar si el intento fue exitoso';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM usuario WHERE id_usuario = p_id_usuario) THEN
        RAISE EXCEPTION 'El usuario % no existe', p_id_usuario;
    END IF;

    INSERT INTO log_inicio_sesion (id_usuario, resultado, fecha)
    VALUES (
        p_id_usuario,
        CASE WHEN p_exitoso THEN 'EXITOSO' ELSE 'FALLIDO' END,
        localtimestamp
    )
    RETURNING id_log INTO v_id_log;

    RETURN v_id_log;
END;
$$;
